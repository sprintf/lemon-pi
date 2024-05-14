from typing import Optional

from gps import *

from dateutil import parser
from lemon_pi.car.display_providers import SpeedProvider, PositionProvider
from lemon_pi.car.updaters import PositionUpdater
from threading import Thread
from lemon_pi.car.event_defs import (
    ExitApplicationEvent,
    NotMovingEvent,
    MovingEvent,
    GPSConnectedEvent,
    GPSDisconnectedEvent
)
import logging
import time
import os

from lemon_pi.shared.data_provider_interface import GpsProvider, GpsPos
from lemon_pi.shared.events import EventHandler
from lemon_pi.shared.usb_detector import UsbDetector

logger = logging.getLogger(__name__)


class GpsReader(Thread, SpeedProvider, PositionProvider, EventHandler, GpsProvider):

    def __init__(self, log_to_file=False):
        Thread.__init__(self, daemon=True)
        self.fix_timestamp = 0
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
                session = gps()
                self.init_gps_connection(session)

                while not self.finished:
                    try:
                        data = session.next()

                        if session.fix.time and str(session.fix.time) != "nan":
                            logger.debug("{} {} {} {}".
                                         format(session.fix.time,
                                                data['class'],
                                                session.fix.latitude,
                                                session.fix.longitude))
                            gps_datetime = parser.isoparse(session.fix.time).astimezone()
                            if gps_datetime.year < 2021:
                                logger.debug("time wonky, ignoring")
                                continue
                            gps_tstamp = gps_datetime.timestamp()
                        else:
                            gps_tstamp = time.time()

                        if session.fix.status == STATUS_NO_FIX:
                            # losing a gps fix doesn't emit a GPSDisconnected event ..
                            # we can look into whether it should or not once we have empirical information
                            logger.warning("no fix...awaiting")
                            self.time_synced = False
                            # don't sleep as we want to quickly traverse these messages until we find one that is synced
                            # do need to test battery drain without this, but it should be fine.
                            # time.sleep(0.5)
                            continue

                        self.time_synced = True

                        if data['class'] == 'TPV':
                            # assuming its coming in m/s
                            if not math.isnan(session.fix.speed):
                                self.speed_mph = int(session.fix.speed * 2.237)
                                if self.speed_mph < 3:
                                    NotMovingEvent.emit(speed=self.speed_mph,
                                                        lat_long=(session.fix.latitude, session.fix.longitude))
                                else:
                                    MovingEvent.emit(speed=self.speed_mph,
                                                     lat_long=(session.fix.latitude, session.fix.longitude))
                            if not math.isnan(session.fix.track):
                                self.heading = int(session.fix.track)
                            if not math.isnan(session.fix.latitude):
                                self.lat = session.fix.latitude
                                self.long = session.fix.longitude
                                self.fix_timestamp = time.time()
                                # generally we should try to move away from position listeners, and instead
                                # have them pull from this class when they need it
                                if self.position_listener:
                                    start_time = time.time()
                                    try:
                                        self.position_listener.update_position(self.lat, self.long,
                                                                               self.heading, gps_tstamp,
                                                                               self.speed_mph)
                                    except Exception:
                                        logger.exception("issue with GPS listener.")
                                    finally:
                                        elapsed_ms = int(time.time() - start_time * 1000)
                                        if elapsed_ms > 50:
                                            logger.warning(f"position handling took {elapsed_ms} ms")
                                if not self.working:
                                    self.working = True
                                    GPSConnectedEvent.emit()
                    except KeyError:
                        # this happens when elevation is not included, we don't care
                        pass
            except Exception:
                logger.exception("issue with GPS, reconnecting.")
                self.working = False
                GPSDisconnectedEvent.emit()
                time.sleep(10)

    def get_speed(self) -> int:
        if self.time_synced and time.time() - self.fix_timestamp < 5:
            return self.speed_mph
        else:
            return 999

    def get_heading(self) -> int:
        if self.time_synced and time.time() - self.fix_timestamp < 5:
            return int(self.heading)
        else:
            return 0

    def get_lat_long(self) -> (float, float):
        if self.time_synced and time.time() - self.fix_timestamp < 5:
            return self.lat, self.long
        else:
            return 0.0, 0.0

    def get_gps_position(self) -> Optional[GpsPos]:
        if self.time_synced and time.time() - self.fix_timestamp < 5:
            return GpsPos(self.lat, self.long, int(self.heading), self.speed_mph, self.fix_timestamp)
        else:
            return None

    def is_working(self) -> bool:
        return self.working

    def register_position_listener(self, listener: PositionUpdater):
        self.position_listener = listener

    @staticmethod
    def init_gps_connection(session: gps):
        # read anything that's out there
        session.read()
        session.send('?DEVICES;')
        code = session.read()
        logger.debug(f"got code {code}")
        response = session.response
        logger.debug(f"got response {response}")
        devices = response['devices']
        if len(devices) == 0 or "'native': 1" in str(response):
            session.close()
            logger.warning(f"response = {response}")
            raise Exception("no gps device or it's in the wrong mode")
        session.send('?WATCH={"enable":true,"json":true}')


if __name__ == "__main__":

    if "SETTINGS_MODULE" not in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_car"

    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)


    class FileLogger(PositionUpdater):

        def __init__(self):
            self.file = open("traces/trace-{}.csv".format(int(time.time())), mode="w")

        def update_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int) -> None:
            diff = int((time.time() - tstamp) * 1000)
            print(f"diff between now and gps time = {diff}ms")
            #self.file.write("{},{},{},{},{}\n".format(tstamp, lat, long, heading, speed))
            #self.file.flush()


    UsbDetector.init()
    tracker = GpsReader()
    tracker.call_gpsctl()
    tracker.register_position_listener(FileLogger())
    tracker.run()
