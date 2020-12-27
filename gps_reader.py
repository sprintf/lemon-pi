from gps import *

from display_providers import SpeedProvider, PositionProvider
from updaters import PositionUpdater
from threading import Thread
import logging
import time

logger = logging.getLogger(__name__)

class GpsReader(Thread, SpeedProvider, PositionProvider):

    def __init__(self, log_to_file=False):
        Thread.__init__(self)
        self.speed_mph = 999
        self.heading = 0
        self.working = False
        self.lat = 0.0
        self.long = 0.0
        self.position_listener = None
        self.log = log_to_file

    def run(self) -> None:
        while True:
            try:
                logger.info("connecting to GPS...")
                session = gps(mode=WATCH_ENABLE)

                while True:
                    try:
                        data = session.next()
                        if data['class'] == 'TPV':
                            # print('lat lon = {} {} speed = {} time = {} track = {}'.
                            #       format(session.fix.latitude,
                            #              session.fix.longitude,
                            #              session.fix.speed,
                            #              session.fix.time,
                            #              session.fix.track))

                            if session.fix.status != STATUS_NO_FIX:
                                # assuming its coming in m/s
                                if not math.isnan(session.fix.speed):
                                    self.speed_mph = int(session.fix.speed * 2.237)
                                if not math.isnan(session.fix.track):
                                    self.heading = session.fix.track
                                if not math.isnan(session.fix.latitude):
                                    self.lat = session.fix.latitude
                                    self.long = session.fix.longitude
                                    if self.position_listener:
                                        self.position_listener.update_position(self.lat, self.long, self.heading, time.time(), self.speed_mph)
                                    self.working = True
                                # todo : get this so its accurate
                                # timestamp = float((session.fix.time - datetime(1970,1,1)).total_seconds())
                            time.sleep(0.1)
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



