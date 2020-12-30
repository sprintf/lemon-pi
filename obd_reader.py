import obd
from obd import OBDResponse
import time, sys
import logging

from threading import Thread
from display_providers import TemperatureProvider
from updaters import MafUpdater
from events import OBDConnectedEvent, OBDDisconnectedEvent

logger = logging.getLogger(__name__)

class ObdReader(Thread, TemperatureProvider):

    refresh_rate = {
        obd.commands.COOLANT_TEMP: 10,
        obd.commands.MAF: 0.1,
    }

    def __init__(self, maf_listener: MafUpdater):
        Thread.__init__(self)
        self.working = False
        self.temp_f = 0
        self.last_update_time = {}
        self.maf_listener = maf_listener

        for key in ObdReader.refresh_rate.keys():
            self.last_update_time[key] = 0.0

    def run(self) -> None:
        while True:
            try:
                connection = self.connect()
                if connection is None:
                    time.sleep(10)
                    continue

                while connection.status() == obd.OBDStatus.CAR_CONNECTED:
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
                print("bad stuff in OBD land %s", e)
                self.working = False
                OBDDisconnectedEvent()
                time.sleep(10)

    def connect(self):
        ports = obd.scan_serial()
        usb = ""
        logger.info("ports = " + str(ports))
        for port in ports:
            if port.find('usbserial') > 0:
                usb = port
        if usb == "":
            return None

        result = obd.OBD(usb, protocol="3")
        OBDConnectedEvent.emit()
        result.print_commands()

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
            # grab the value in grams per second
            self.maf_listener.update_maf(response.value.to('gps').magnitude, response.time)
        else:
            raise RuntimeWarning("no handler for {}".format(cmd))

    def get_temp_f(self) -> int:
        return self.temp_f

    def is_working(self) -> bool:
        return self.working

if __name__ == "__main__":
    ObdReader().run()

