import obd
from obd import OBDResponse
import time
import os
import logging
import platform

from threading import Thread
from python_settings import settings

from lemon_pi.car.display_providers import TemperatureProvider
from lemon_pi.car.updaters import FuelUsageUpdater
from lemon_pi.car.event_defs import OBDConnectedEvent, OBDDisconnectedEvent, ExitApplicationEvent
from lemon_pi.shared.usb_detector import UsbDetector, UsbDevice

logger = logging.getLogger(__name__)


#
#  useful reading : https://www.autoserviceprofessional.com/articles/6237-fuel-trim-how-it-works-and-how-to-make-it-work-for-you
#
# Fuel mass = Air mass x (short-term fuel trim x long-term fuel trim) divided by (equivalence ratio x 14.64)
#
# Although, I add the short and long term fuel trims together as it makes more sense (to me)
#
class ObdReader(Thread, TemperatureProvider):

    refresh_rate = {
        obd.commands.COOLANT_TEMP: 10,
#        obd.commands.FUEL_STATUS: 1,
#        obd.commands.LONG_FUEL_TRIM_1: 10,
#        obd.commands.SHORT_FUEL_TRIM_1: 0.1,
        obd.commands.MAF: 0.2,
    }

    def __init__(self, fuel_listener: FuelUsageUpdater):
        Thread.__init__(self)
        self.working = False
        self.no_data_count = 0
        self.temp_f = 0
        # the time the temperature was last read from OBD
        self.temp_time = 0
        self.short_term_fuel_trim = 0.0
        self.long_term_fuel_trim = 0.0
        self.last_update_time = {}
        self.fuel_listener = fuel_listener
        self.finished = False
        self.is_rpi = platform.system() == "Linux"
        ExitApplicationEvent.register_handler(self)

        for key in ObdReader.refresh_rate.keys():
            self.last_update_time[key] = 0.0

    def handle_event(self, event, **kwargs):
        if event == ExitApplicationEvent:
            self.finished = True

    def run(self) -> None:
        connection = None
        while not self.finished:
            try:
                connection = self.connect(connection)
                if connection is None:
                    logger.info("no connection, waiting 30s")
                    time.sleep(30)
                    continue
                self.no_data_count = 0

                while connection.status() == obd.OBDStatus.CAR_CONNECTED and not self.finished:
                    now = time.time()
                    for cmd in ObdReader.refresh_rate.keys():
                        if now - self.last_update_time[cmd] > ObdReader.refresh_rate[cmd]:
                            r = connection.query(cmd)
                            if not r.is_null():
                                self.working = True
                                self.last_update_time[cmd] = r.time
                                self.process_result(cmd, r)
                                self.no_data_count = 0
                            else:
                                logger.info("no data, waiting")
                                time.sleep(0.5)
                                # after 10 of these close the connection
                                self.no_data_count += 1
                                if self.no_data_count > 10:
                                    logger.info("giving up")
                                    connection.close()
                    # I think we need MAF as fast as poss
                    # time.sleep(1)
            except Exception as e:
                logger.exception("bad stuff in OBD land %s", e)
                if connection:
                    connection.close()
                self.working = False
                OBDDisconnectedEvent.emit()
                time.sleep(10)

    def connect(self, old_connection):
        port = UsbDetector.get(UsbDevice.OBD)
        if not port:
            return None

        if old_connection:
            OBDDisconnectedEvent.emit()
            old_connection.close()

        result = obd.OBD(port, protocol=settings.OBD_PROTOCOL, fast=True)
        status = result.status()
        if status != obd.OBDStatus.CAR_CONNECTED:
            result.close()
            return None

        time.sleep(0.5)

        cmds = result.query(obd.commands.PIDS_A)
        if cmds.value:
            logger.debug("available PIDS_A commands {}".format(cmds.value))
            OBDConnectedEvent.emit()
            return result
        else:
            result.close()

        return None

    def process_result(self, cmd, response: OBDResponse):
        if response.value is None:
            return
        logger.debug("processing {} at {}".format(cmd, response))
        if cmd == obd.commands.COOLANT_TEMP:
            self.temp_f = int(response.value.to('degF').magnitude)
            self.temp_time = response.time
        elif cmd == obd.commands.MAF:
            fuel_usage = self.calc_fuel_rate(response.value.to('gps').magnitude,
                                             settings.FUEL_FIDDLE_PERCENT)
            self.fuel_listener.update_fuel(fuel_usage, response.time)
        elif cmd == obd.commands.SHORT_FUEL_TRIM_1:
            if response.value:
                self.short_term_fuel_trim = response.value.magnitude
        elif cmd == obd.commands.LONG_FUEL_TRIM_1:
            if response.value:
                self.long_term_fuel_trim = response.value.magnitude
        elif cmd == obd.commands.FUEL_STATUS:
            pass

        else:
            raise RuntimeWarning("no handler for {}".format(cmd))

    def get_temp_f(self) -> int:
        if time.time() - self.temp_time > 60:
            return -1
        return self.temp_f

    def is_working(self) -> bool:
        return self.working

    def calc_fuel_rate(self, maf_value, fuel_fiddle_percent):
        raw_fuel_mass = maf_value / 14.64
        trim_adjustment = raw_fuel_mass * ((self.short_term_fuel_trim + self.long_term_fuel_trim) / 100)
        adjusted_fuel_mass = raw_fuel_mass + trim_adjustment
        ml_per_second = adjusted_fuel_mass * (1000/757)
        if fuel_fiddle_percent != 0:
            adjustment = ml_per_second * (fuel_fiddle_percent / 100)
            ml_per_second += adjustment
        return ml_per_second


if __name__ == "__main__":

    if "SETTINGS_MODULE" not in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_car"

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    class OBDLogger(FuelUsageUpdater):

        def update_fuel(self, ml_per_second: float, time: float):
            print("Fuel: {:.2f} ml per sec".format(ml_per_second))

    UsbDetector.init()
    ObdReader(OBDLogger()).run()
