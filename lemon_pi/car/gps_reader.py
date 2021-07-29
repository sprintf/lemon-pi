from gps import *

from dateutil import parser
from datetime import datetime, timezone, timedelta
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
import subprocess
from python_settings import settings

from lemon_pi.shared.data_provider_interface import GpsProvider
from lemon_pi.shared.events import EventHandler
from lemon_pi.shared.generated.messages_pb2 import GpsPosition


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
        self.part_synced = False
        self.time_synced = False
        self.sequential_timesync_errors = 0
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
                            logger.debug("{} {} {} {}".format(session.fix.time, data['class'], session.fix.latitude, session.fix.longitude ))
                            gps_datetime = parser.isoparse(session.fix.time).astimezone()
                            lag: timedelta = abs(datetime.now(tz=timezone.utc) - \
                                                 gps_datetime)

                            if self.part_synced:
                                # we have set the clock to the GPS a moment ago...whatever
                                # the drift is due to the time taken to set the system clock
                                logger.info("fine tuning clock from GPS by {}...".format(lag.seconds))
                                epoch = int(gps_datetime.timestamp()) + lag.seconds
                                subprocess.run(['sudo', 'date', '-u', '-s' '@{}'.format(epoch)])
                                logger.info("time adjusted to {}".format(datetime.now()))
                                self.part_synced = False
                                self.time_synced = True
                                self.sequential_timesync_errors = 0
                                continue

                            # we find there's a 1s difference between SKY and TPV messages that
                            # come in.  We could ignore SKY, but for now we allow a 2s drift
                            if lag.total_seconds() > 2:
                                self.sequential_timesync_errors += 1
                                if (lag.total_seconds() > 30 or self.sequential_timesync_errors > 30) \
                                        and not self.time_synced:
                                    logger.info("setting clock from GPS...")
                                    epoch = int(gps_datetime.timestamp())
                                    subprocess.run(['sudo', 'date', '-u', '-s' '@{}'.format(epoch)])
                                    self.part_synced = True
                                    logger.info("time corrected to {}".format(datetime.now()))
                                else:
                                    logger.warning("GPS Data time lag = {}  (skipping {}/30)".
                                                   format(lag.total_seconds(), self.sequential_timesync_errors))
                                continue
                            self.sequential_timesync_errors = 0
                            self.time_synced = True

                        if session.fix.status == STATUS_NO_FIX:
                            # losing a gps fix doesn't emit a GPSDisconnected event ..
                            # we can look into whether it should or not once we have empirical information
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
                                self.fix_timestamp = time.time()
                                # generally we should try to move away from position listeners, and instead
                                # have them pull from this class when they need it
                                if self.position_listener:
                                    self.position_listener.update_position(self.lat, self.long, self.heading, time.time(), self.speed_mph)
                                if not self.working:
                                    self.working = True
                                    GPSConnectedEvent.emit()
                            #time.sleep(0.1)
                    except KeyError:
                        # this happens when elevation is not included, we don't care
                        pass
            except Exception as e:
                logger.exception("issue with GPS, reconnecting.")
                self.working = False
                GPSDisconnectedEvent.emit()
                time.sleep(30)

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
            return (self.lat, self.long)
        else:
            return (0.0, 0.0)

    def get_gps_position(self) -> GpsPosition:
        if self.time_synced and time.time() - self.fix_timestamp < 5:
            result = GpsPosition()
            result.lat = self.lat
            result.long = self.long
            result.speed_mph = self.speed_mph
            result.heading = self.heading
            result.gps_timestamp = round(self.fix_timestamp)
            return result
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
        logger.debug("got code {}".format(code))
        response = session.data
        logger.debug("got response {}".format(response))
        devices = response['devices']
        if len(devices) == 0:
            raise Exception("no gps device")
        gps = devices[0]
        if 'driver' in gps:
            logger.info("detected GPS device, setting baud rate to 57600")
            # setting cycle to more than 1.0 means we see the same coordinate
            # position delivered multiple times in a row
            session.send(f'?DEVICE=\{"class":"DEVICE","bps":57600,"cycle":{settings.GPS_CYCLE}\}')
            code = session.read()
            logger.debug("got code {}".format(code))
            response = session.data
            logger.debug("got response {}".format(response))
        session.send('?WATCH={"enable":true,"json":true}')


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    class FileLogger(PositionUpdater):

        def __init__(self):
            self.file = open("traces/trace-{}.csv".format(int(time.time())), mode="w")

        def update_position(self, lat:float, long:float, heading:float, time:float, speed:int) -> None:
            self.file.write("{},{},{},{},{}\n".format(time, lat, long, heading, speed))
            self.file.flush()

    tracker = GpsReader()
    tracker.register_position_listener(FileLogger())
    tracker.run()



