import platform
from typing import Optional

from lemon_pi.car.gps_geometry import crossed_line
from lemon_pi.car.predictor import LapTimePredictor
from lemon_pi.car.track import TrackLocation, START_FINISH
from lemon_pi.car.updaters import PositionUpdater
from lemon_pi.car.display_providers import LapProvider
from lemon_pi.car.event_defs import (
    LeaveTrackEvent,
    CompleteLapEvent,
    RadioSyncEvent,
    LapInfoEvent, EnterTrackEvent, ResetFastLapEvent, ReverseTrackEvent
)

import time
from datetime import datetime
import logging
from python_settings import settings

from lemon_pi.shared.data_provider_interface import GpsPos
from lemon_pi.shared.events import EventHandler

logger = logging.getLogger(__name__)
gps_logger = logging.getLogger("gps-logger")
lap_logger = logging.getLogger("lap-logger")


class LapTracker(PositionUpdater, LapProvider, EventHandler):

    def __init__(self, track: TrackLocation):
        self.track = track
        self.on_track = False
        self.lap_start_time = time.time()
        self.last_gps = None
        self.lap_count = 999
        self.stint_lap_count = 0
        self.last_log_time = 0
        self.last_lap_time = 0
        self.best_lap_time: Optional[float] = None
        self.last_timestamp = 0
        self.last_dist_to_line = 0
        self.predictive_lap_timer = LapTimePredictor(track.get_start_finish_target())
        self.extra_handlers: [PositionUpdater] = []
        LapInfoEvent.register_handler(self)
        LeaveTrackEvent.register_handler(self)
        EnterTrackEvent.register_handler(self)
        ResetFastLapEvent.register_handler(self)

    def add_position_handler(self, p: PositionUpdater):
        self.extra_handlers.append(p)

    def update_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int) -> None:
        if self.last_gps and (lat, long) == (self.last_gps.lat, self.last_gps.long):
            return
        self.process_position(lat, long, heading, tstamp, speed)
        for handler in self.extra_handlers:
            try:
                handler.update_position(lat, long, heading, tstamp, speed)
            except Exception:
                logger.exception("problem updating position")

    def process_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int) -> None:
        this_gps = GpsPos(lat, long, heading, speed, tstamp)
        try:
            logger.debug("updating position to {} {}".format(lat, long))
            crossed_start_finish, cross_time, backwards = \
                self.predictive_lap_timer.update_position(lat, long, heading, tstamp)
            if crossed_start_finish:
                if backwards:
                    self.track.reverse()
                    ReverseTrackEvent.emit()

                # de-bounce hitting start finish line twice ... a better
                # approach might be to ensure car travels so far away from line
                if tstamp - self.lap_start_time > 10:
                    lap_time = cross_time - self.lap_start_time
                    # something is creating weird vals in here
                    if lap_time < 0 or lap_time > 1000000:
                        logger.warning(f"got a stupid lap time {cross_time} - {self.lap_start_time}")
                        lap_time = 0
                    CompleteLapEvent.emit(lap_count=self.lap_count + 1, lap_time=lap_time)
                    if not self.on_track:
                        logger.info("entering track")
                        # this isn't true for a multi-driver day, but we'll keep each
                        # drivers view as their own
                        self.lap_count = 0
                        self.stint_lap_count = 0
                        self.on_track = True
                    else:
                        logger.info("completed lap!")
                        self.lap_count += 1
                        self.stint_lap_count += 1
                        self.last_lap_time = lap_time
                        if lap_time > 0 and (self.best_lap_time is None or lap_time < self.best_lap_time):
                            self.best_lap_time = lap_time
                        lap_logger.info(f"{self.lap_count},{self.last_lap_time:.1f}")
                    self.lap_start_time = cross_time

                    RadioSyncEvent.emit(ts=cross_time)
            else:
                for target_metadata in self.track.targets.keys():
                    target = self.track.targets[target_metadata]
                    if target:
                        if target_metadata != START_FINISH:
                            crossed_target, cross_time, backwards = \
                                crossed_line(self.last_gps, this_gps, target)
                            if crossed_target:
                                if backwards:
                                    target_metadata.backwards_event.emit(ts=cross_time)
                                    self.track.reverse()
                                    ReverseTrackEvent.emit()
                                else:
                                    target_metadata.event.emit(ts=cross_time)
                                break
            # log gps
            if settings.LOG_GPS:
                # defend against high speed logging here
                if tstamp - self.last_log_time < 1:
                    return
                dt = datetime.fromtimestamp(tstamp)
                gps_logger.info(
                    f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}.{int(dt.microsecond * 1000):03d},{tstamp},"
                    f"{self.lap_count},{lat},{long},{speed},{heading}")
                self.last_log_time = tstamp
        finally:
            self.last_gps = this_gps

    def handle_event(self, event, lap_count=0, ts=0):
        if event == LapInfoEvent:
            # the lap info tells us the last lap completed, but this
            # lap timer is showing the next lap, so we add one to it
            self.lap_count = lap_count + 1

            # this only gets hit in simulation mode when the car is not
            # actually running. It lets us see some lap time data when
            # testing out a pre-recorded feed
            if not self.on_track and platform.system() == "Darwin" :
                self.last_lap_time = ts - self.lap_start_time
                self.lap_start_time = ts
        if event == LeaveTrackEvent:
            self.on_track = False
        if event == EnterTrackEvent:
            self.on_track = True
            if ts == 0.0:
                self.lap_start_time = time.time()
            else:
                self.lap_start_time = ts
            if self.lap_count == 999:
                self.lap_count = 0
            self.stint_lap_count = 0
        if event == ResetFastLapEvent:
            self.best_lap_time = None

    def get_lap_count(self) -> int:
        return self.lap_count

    def get_stint_lap_count(self) -> int:
        return self.stint_lap_count

    def get_lap_timer(self) -> int:
        return int(time.time() - self.lap_start_time)

    def get_last_lap_time(self) -> float:
        return self.last_lap_time

    def get_predicted_lap_time(self) -> Optional[float]:
        return self.predictive_lap_timer.predict_lap()

    def get_best_lap_time(self) -> Optional[float]:
        return self.best_lap_time


if __name__ == "__main__":
    import csv
    from lemon_pi.car.track import read_tracks

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    tracks = read_tracks()

    tracker = LapTracker(tracks[1])
    with open("traces/trace-1608347418.csv") as csvfile:
        points = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        x = 0
        for point in points:
            x += 1
            if x % 1 == 0:
                label = "hdg:{} spd:{}".format(int(point[3]), "?")
                tracker.update_position(float(point[1]), float(point[2]), float(point[3]), float(point[0]), 30)
