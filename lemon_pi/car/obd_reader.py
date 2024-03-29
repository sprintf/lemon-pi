import obd
from obd import OBDResponse
import time
import os
import logging
import platform

from threading import Thread
from python_settings import settings

from lemon_pi.car.display_providers import TemperatureProvider, FuelProvider
from lemon_pi.car.event_defs import OBDConnectedEvent, OBDDisconnectedEvent, ExitApplicationEvent
from lemon_pi.shared.usb_detector import UsbDetector, UsbDevice

logger = logging.getLogger(__name__)


class ObdReader(Thread, TemperatureProvider, FuelProvider):

    refresh_rate = {
        obd.commands.COOLANT_TEMP: 10,
        # temporarily deleting this
        # obd.commands.FUEL_LEVEL: 10,
    }

    def __init__(self):
        Thread.__init__(self)
        self.working = False
        self.temp_f = 0
        self.initialization_time = time.time()
        # the time the temperature was last read from OBD
        self.temp_time = 0
        self.fuel_level = 100
        self.fuel_level_time = 0
        self.last_update_time = {}
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

                while connection.status() != obd.OBDStatus.CAR_CONNECTED and not self.finished:
                    time.sleep(30)

                self.initialization_time = time.time()

                no_data_cycles = 0
                while connection.status() == obd.OBDStatus.CAR_CONNECTED and not self.finished:
                    now = time.time()
                    keys_to_delete = []
                    for cmd in ObdReader.refresh_rate.keys():
                        if now - self.last_update_time[cmd] > ObdReader.refresh_rate[cmd]:
                            r = connection.query(cmd)
                            if not r.is_null():
                                no_data_cycles = 0
                                self.working = True
                                self.last_update_time[cmd] = r.time
                                self.process_result(cmd, r)
                            else:
                                no_data_cycles += 1
                                logger.info(f"no data, for {cmd} ({no_data_cycles}/5)")
                                # keep trying for 5 minutes, then remove the setting
                                if self.last_update_time[cmd] == 0.0 and time.time() - self.initialization_time > 300:
                                    # we never got any data for this command, remove it
                                    keys_to_delete.append(cmd)
                                time.sleep(10)
                                if no_data_cycles == 5:
                                    raise Exception("forcing reconnect due to data starvation")
                    time.sleep(0.5)
                    # leaving this functionality out for now, seems fragile and harmful
                    # for dead_key in keys_to_delete:
                    #     del ObdReader.refresh_rate[dead_key]
                    #     logger.info(f"removed {dead_key}")

            except Exception as e:
                logger.exception("bad stuff in OBD land %s", e)
                if connection:
                    connection.close()
                self.working = False
                OBDDisconnectedEvent.emit()
                time.sleep(10)

    def connect(self, old_connection):
        if not UsbDetector.detected(UsbDevice.OBD):
            return None

        port = UsbDetector.get(UsbDevice.OBD)
        if not port:
            return None

        if old_connection:
            OBDDisconnectedEvent.emit()
            old_connection.close()

        result = obd.OBD(port, protocol=settings.OBD_PROTOCOL, fast=settings.OBD_FAST)
        status = result.status()
        if status != obd.OBDStatus.CAR_CONNECTED:
            result.close()
            return None

        logger.info("Car Connected")
        time.sleep(0.5)

        cmds = result.query(obd.commands.PIDS_A)
        if cmds.value:
            logger.info(f"available PIDS_A commands {cmds.value}")
            OBDConnectedEvent.emit()
            cmds = result.query(obd.commands.PIDS_B)
            if cmds.value:
                logger.info(f"available PIDS_B commands {cmds.value}")
            return result
        else:
            logger.info("no response to PIDS_A command")
            result.close()

        return None

    def process_result(self, cmd, response: OBDResponse):
        if response.value is None:
            return
        logger.debug(f"processing {cmd} at {response}")
        if cmd == obd.commands.COOLANT_TEMP:
            self.temp_f = int(response.value.to('degF').magnitude)
            self.temp_time = response.time
        elif cmd == obd.commands.FUEL_LEVEL:
            if response.value:
                self.fuel_level = int(response.value.magnitude)
                self.fuel_level_time = response.time
        else:
            raise RuntimeWarning(f"no handler for {cmd}")

    def get_temp_f(self) -> int:
        if time.time() - self.temp_time > 60:
            return -1
        return self.temp_f

    def get_fuel_percent_remaining(self) -> int:
        # todo : see if it's been updated recently
        return self.fuel_level

    def is_working(self) -> bool:
        return self.working


if __name__ == "__main__":

    if "SETTINGS_MODULE" not in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_car"

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    UsbDetector.init()
    ObdReader().run()
