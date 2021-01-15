import obd
from obd import OBDResponse
import time
import logging
import platform

from threading import Thread
from display_providers import TemperatureProvider
from updaters import FuelUsageUpdater
from events import OBDConnectedEvent, OBDDisconnectedEvent, ExitApplicationEvent

logger = logging.getLogger(__name__)


##
##  useful reading : https://www.autoserviceprofessional.com/articles/6237-fuel-trim-how-it-works-and-how-to-make-it-work-for-you
##
## Fuel mass = Air mass x (short-term fuel trim x long-term fuel trim) divided by (equivalence ratio x 14.64)
##
## Although, I add the short and long term fuel trims together as it makes more sense (to me)
##
class ObdReader(Thread, TemperatureProvider):

    refresh_rate = {
        obd.commands.COOLANT_TEMP: 10,
        obd.commands.LONG_FUEL_TRIM_1: 10,
        obd.commands.SHORT_FUEL_TRIM_1: 0.1,
        obd.commands.MAF: 0.1,
    }

    def __init__(self, fuel_listener: FuelUsageUpdater):
        Thread.__init__(self)
        self.working = False
        self.temp_f = 0
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
        while not self.finished:
            try:
                connection = self.connect()
                if connection is None:
                    time.sleep(10)
                    continue

                while connection.status() == obd.OBDStatus.CAR_CONNECTED and not self.finished:
                    now = time.time()
                    for cmd in ObdReader.refresh_rate.keys() :
                        if now - self.last_update_time[cmd] > ObdReader.refresh_rate[cmd]:
                            r = connection.query(cmd)
                            if r is not None:
                                self.working = True
                                self.last_update_time[cmd] = r.time
                                self.process_result(cmd, r)
                    # I think we need MAF as fast as poss
                    #time.sleep(1)
            except Exception as e:
                logger.exception("bad stuff in OBD land %s", e)
                self.working = False
                OBDDisconnectedEvent.emit()
                time.sleep(10)

    def connect(self):
        ports = obd.scan_serial()
        usb = ""
        logger.info("ports = " + str(ports))
        for port in ports:
            if self.is_rpi:
                if port.find('USB0'):
                    usb = port
            else:  # mac / darwin
                if port.find('usbserial') > 0:
                    usb = port
        if usb == "":
            return None

        # TODO : this should move into settings now we have them
        result = obd.OBD(usb, protocol="3")
        OBDConnectedEvent.emit()
        # result.print_commands()

        cmds = result.query(obd.commands.PIDS_A)
        logger.debug("available PIDS_A commands {}".format(cmds.value))

        cmds = result.query(obd.commands.PIDS_B)
        logger.debug("available PIDS_B commands {}".format(cmds.value))

        cmds = result.query(obd.commands.PIDS_C)
        logger.debug("available PIDS_C commands {}".format(cmds.value))

        return result

    def process_result(self, cmd, response: OBDResponse):
        logger.debug("processing {} at {}".format(cmd, response))
        if cmd == obd.commands.COOLANT_TEMP:
            self.temp_f = int(response.value.to('degF').magnitude)
        elif cmd == obd.commands.MAF:
            fuel_usage = self.calc_fuel_rate(response.value.to('gps').magnitude)
            self.fuel_listener.update_fuel(fuel_usage, response.time)
        elif cmd == obd.commands.SHORT_FUEL_TRIM_1:
            if response.value:
                self.short_term_fuel_trim = response.value.magnitude
        elif cmd == obd.commands.LONG_FUEL_TRIM_1:
            if response.value:
                self.long_term_fuel_trim = response.value.magnitude
        else:
            raise RuntimeWarning("no handler for {}".format(cmd))

    def get_temp_f(self) -> int:
        return self.temp_f

    def is_working(self) -> bool:
        return self.working

    def calc_fuel_rate(self, maf_value):
        raw_fuel_mass = maf_value / 14.64
        trim_adjustment = raw_fuel_mass * ((self.short_term_fuel_trim + self.long_term_fuel_trim) / 100)
        adjusted_fuel_mass = raw_fuel_mass + trim_adjustment
        # todo : weight a liter of '91 grade gas ... allegedly it weights about 750 grams
        ml_per_second = adjusted_fuel_mass * (1000/750)
        return ml_per_second

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    class OBDLogger(FuelUsageUpdater):

        def update_fuel(self, ml_per_second:float, time:float):
            print("Fuel: {:.2f} ml per sec".format(ml_per_second))

    ObdReader(OBDLogger()).run()

