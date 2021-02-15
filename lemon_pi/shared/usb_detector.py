
import platform
import glob
import os
import logging
import serial
import time
from enum import Enum

logger = logging.getLogger(__name__)


class UsbDevice(Enum):
    OBD = 1
    LORA = 2


# it's hard to tell which device is plugged into the computer ... either on
# Raspian or on Mac.
#
# This class attempts to solve this by scanning the serial ports that appear to be
# candidates and then querying the interface to try to figure out what is what
class UsbDetector:

    __instance = None

    def __init__(self):
        self.usb_map : {UsbDevice, str} = {}
        self.device_map : {str, UsbDevice} = {}
        self.last_scan_time = 0

    @classmethod
    def init(cls):
        UsbDetector.__instance = UsbDetector()
        UsbDetector.__instance.__scan__()

    @classmethod
    def get_instance(cls):
        return UsbDetector.__instance

    @classmethod
    def get(cls, device_type:UsbDevice):
        return UsbDetector.__instance.usb_map[device_type]

    def __scan__(self):
        glob_pattern = self.__get_dev_pattern__()
        devices = glob.glob(glob_pattern)
        logger.info("found usb serial devices : {}".format(devices))

        # step 0 ... throw out already classified
        for device in devices:
            if os.path.getctime(device) < self.last_scan_time:
                logger.info("already mapped : {}".format(device))
                devices.remove(device)

        # step1 ... see if any are radio
        logger.info("detecting Lora devices")
        for device in devices:
            with serial.Serial(device, baudrate=57600, timeout=2) as ser:
                try:
                    while len(ser.readline()):
                        logger.debug("throwing away... ")
                        pass
                    ser.write("sys get ver\r\n".encode("UTF-8"))
                    time.sleep(0.5)
                    # set timeout ...? ?
                    resp_bytes = ser.readline()
                    logger.info(resp_bytes)
                    if resp_bytes:
                        resp = resp_bytes.decode("UTF-8")
                        if resp.startswith("RN2903"):
                            self.usb_map[UsbDevice.LORA] = device
                            self.device_map[device] = UsbDevice.LORA
                            logger.info("associated {} with Lora".format(device))

                except UnicodeDecodeError:
                    # we get into this when we try to talk to OBD like this
                    pass
                finally:
                    ser.close()

        logger.info("detecting OBD devices")
        for device in devices:
            if self.device_map.get(device):
                # it's been identified as Lora
                continue
            with serial.Serial(device, baudrate=38400, timeout=2) as ser:
                try:
                    ser.write("atz\r\r".encode("UTF-8"))
                    time.sleep(0.5)
                    resp_bytes = ser.readline()
                    logger.info(resp_bytes)
                    if "ELM327" in str(resp_bytes):
                        self.usb_map[UsbDevice.OBD] = device
                        self.device_map[device] = UsbDevice.OBD
                        logger.info("associated {} with OBD".format(device))
                finally:
                    ser.close()

        self.last_scan_time = time.time()

    def __get_dev_pattern__(self):
        if platform.system() == "Linux":
            return "/dev/ttyUSB*"
        else:
            return "/dev/tty.usbserial*"


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    UsbDetector.init()
