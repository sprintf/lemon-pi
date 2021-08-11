from lemon_pi.car.predictor import LapTimePredictor
from lemon_pi.car.track import TrackLocation, START_FINISH
from lemon_pi.car.updaters import PositionUpdater, LapUpdater
from lemon_pi.car.display_providers import LapProvider
from lemon_pi.car.event_defs import (
    LeaveTrackEvent,
    CompleteLapEvent,
    RadioSyncEvent,
    LapInfoEvent, EnterTrackEvent
)

import time
from datetime import datetime
import logging
from python_settings import settings

from lemon_pi.shared.events import EventHandler

logger = logging.getLogger(__name__)
gps_logger = logging.getLogger("gps-logger")


class LapTracker(PositionUpdater, LapProvider, EventHandler):

    # todo : add a list of candidate layouts for the track from previous loaded data
    def __init__(self, track: TrackLocation, listener: LapUpdater):
        self.track = track
        self.listener = listener
        self.on_track = False
        self.lap_start_time = time.time()
        self.last_pos = (0, 0)
        self.last_pos_time = 0.0
        self.lap_count = 999
        self.last_lap_time = 0
        self.best_lap_time = None
        self.last_timestamp = 0
        self.last_dist_to_line = 0
        self.predictive_lap_timer = LapTimePredictor(track.get_start_finish_target())
        LapInfoEvent.register_handler(self)
        LeaveTrackEvent.register_handler(self)
        EnterTrackEvent.register_handler(self)

    def update_position(self, lat: float, long: float, heading: float, time: float, speed: int) -> None:
        if (lat, long) == self.last_pos:
            return

        logger.debug("updating position to {} {}".format(lat, long))
        self.last_pos = (lat, long)
        crossed_line, cross_time = self.predictive_lap_timer.update_position(lat, long, heading, time)
        if crossed_line:
            # de-bounce hitting start finish line twice ... a better
            # approach might be to ensure car travels so far away from line
            if time - self.lap_start_time > 10:
                lap_time = cross_time - self.lap_start_time
                CompleteLapEvent.emit(lap_count=self.lap_count + 1, lap_time=lap_time)
                if not self.on_track:
                    logger.info("entering track")
                    # this isn't true for a multi-driver day, but we'll keep each
                    # drivers view as their own
                    self.lap_count = 0
                    self.on_track = True
                    if self.listener:
                        self.listener.update_lap(0, 0)
                else:
                    logger.info("completed lap!")
                    self.lap_count += 1
                    self.last_lap_time = lap_time
                    if self.best_lap_time is None or lap_time < self.best_lap_time:
                        self.best_lap_time = lap_time
                    if self.listener:
                        self.listener.update_lap(self.lap_count, self.last_lap_time)
                self.lap_start_time = cross_time

                RadioSyncEvent.emit(ts=cross_time)
        else:
            for target_metadata in self.track.targets.keys():
                if not target_metadata.multiple:
                    targets = [self.track.targets[target_metadata]]
                else:
                    targets = self.track.targets[target_metadata]
                if target_metadata != START_FINISH:
                    for target in targets:
                        crossed_target, cross_time = \
                            target.line_cross_detector.crossed_line(lat, long, heading, time, target)
                        if crossed_target:
                            target_metadata.event.emit(ts=cross_time)
        # log gps
        if settings.LOG_GPS:
            dt = datetime.fromtimestamp(time)
            gps_logger.info(
                f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d},{time},{self.lap_count},{lat},{long},{speed},{heading}")

    def handle_event(self, event, lap_count=0, ts=0):
        if event == LapInfoEvent:
            # the lap info tells us the last lap completed, but this
            # lap timer is showing the next lap, so we add one to it
            self.lap_count = lap_count + 1

            # this only gets hit in simulation mode when the car is not
            # actually running. It lets us see some lap time data when
            # testing out a pre-recorded feed
            if not self.on_track:
                self.last_lap_time = ts - self.lap_start_time
                self.lap_start_time = ts
        if event == LeaveTrackEvent:
            self.on_track = False
        if event == EnterTrackEvent:
            self.on_track = True
            self.lap_start_time = ts
            if self.lap_count == 999:
                self.lap_count = 0

    def get_lap_count(self) -> int:
        return self.lap_count

    def get_lap_timer(self) -> int:
        return int(time.time() - self.lap_start_time)

    def get_last_lap_time(self) -> float:
        return self.last_lap_time

    def get_predicted_lap_time(self) -> float:
        return self.predictive_lap_timer.predict_lap()

    def get_best_lap_time(self) -> float:
        return self.best_lap_time


if __name__ == "__main__":
    import csv
    from lemon_pi.car.track import read_tracks

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    tracks = read_tracks()

    tracker = LapTracker(tracks[1], None)
    with open("traces/trace-1608347418.csv") as csvfile:
        points = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        x = 0
        for point in points:
            x += 1
            if x % 1 == 0:
                label = "hdg:{} spd:{}".format(int(point[3]), "?")
                tracker.update_position(float(point[1]), float(point[2]), float(point[3]), float(point[0]), 30)
