from gps import *

from dateutil import parser
from datetime import datetime, timezone, timedelta
from display_providers import SpeedProvider, PositionProvider
from updaters import PositionUpdater
from threading import Thread
from events import EventHandler, MovingEvent, NotMovingEvent, CarStoppedEvent, ExitApplicationEvent
import logging
import time
import subprocess

logger = logging.getLogger(__name__)

class GpsReader(Thread, SpeedProvider, PositionProvider, EventHandler):

    def __init__(self, log_to_file=False):
        Thread.__init__(self, daemon=True)
        self.speed_mph = 999
        self.heading = 0
        self.working = False
        self.lat = 0.0
        self.long = 0.0
        self.position_listener = None
        self.log = log_to_file
        self.finished = False
        self.time_synced = False
        ExitApplicationEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == ExitApplicationEvent:
            self.finished = True

    def run(self) -> None:
        while not self.finished:
            try:
                logger.info("connecting to GPS...")
                session = gps(mode=WATCH_ENABLE)

                while not self.finished:
                    try:
                        data = session.next()

                        if session.fix.time and str(session.fix.time) != "nan":
                            logger.debug("{} {} {} {}".format(session.fix.time, data['class'], session.fix.latitude, session.fix.longitude ))
                            gps_datetime = parser.isoparse(session.fix.time).astimezone()
                            lag: timedelta = abs(datetime.now(tz=timezone.utc) - \
                                                 gps_datetime)

                            if lag.total_seconds() > 1:
                                if lag.total_seconds() > 30 and not self.time_synced:
                                    logger.info("setting clock from GPS...")
                                    epoch = int(gps_datetime.timestamp())
                                    subprocess.run(['sudo', 'date', '-u', '-s' '@{}'.format(epoch)])
                                    self.time_synced = True
                                    logger.info("time corrected to {}".format(datetime.now()))
                                else:
                                    logger.warning("GPS Data time lag = {}  (skipping)".format(lag.total_seconds()))
                                continue
                            self.time_synced = True

                        if session.fix.status == STATUS_NO_FIX:
                            logger.warning("no fix...awaiting")
                            time.sleep(0.5)
                            continue

                        if data['class'] == 'TPV':
                            # assuming its coming in m/s
                            if not math.isnan(session.fix.speed):
                                self.speed_mph = int(session.fix.speed * 2.237)
                                if self.speed_mph < 3:
                                    NotMovingEvent.emit(speed=self.speed_mph, lat_long=(session.fix.latitude, session.fix.longitude))
                                else:
                                    MovingEvent.emit(speed=self.speed_mph, lat_long=(session.fix.latitude, session.fix.longitude))
                            if not math.isnan(session.fix.track):
                                self.heading = session.fix.track
                            if not math.isnan(session.fix.latitude):
                                self.lat = session.fix.latitude
                                self.long = session.fix.longitude
                                if self.position_listener:
                                    self.position_listener.update_position(self.lat, self.long, self.heading, time.time(), self.speed_mph)
                                self.working = True
                            #time.sleep(0.1)
                    except KeyError:
                        # this happens when elevation is not included, we don't care
                        pass
            except Exception as e:
                logger.exception("issue with GPS, reconnecting.")
                self.working = False
                time.sleep(10)

    def get_speed(self) -> int:
        return self.speed_mph

    def get_heading(self) -> int:
        return int(self.heading)

    def get_lat_long(self) -> (float, float):
        return (self.lat, self.long)

    def is_working(self) -> bool:
        return self.working

    def register_position_listener(self, listener: PositionUpdater):
        self.position_listener = listener


if __name__ == "__main__":

    class FileLogger(PositionUpdater):

        def __init__(self):
            self.file = open("traces/trace-{}.csv".format(int(time.time())), mode="w")

        def update_position(self, lat:float, long:float, heading:float, time:float, speed:int) -> None:
            self.file.write("{},{},{},{},{}\n".format(time, lat, long, heading, speed))
            self.file.flush()

    tracker = GpsReader()
    tracker.register_position_listener(FileLogger())
    tracker.start()



