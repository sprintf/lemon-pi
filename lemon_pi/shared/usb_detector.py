
import platform
import glob
import os
import logging
import serial
import time
from gps import gps
from enum import Enum

logger = logging.getLogger(__name__)


class UsbDevice(Enum):
    OBD = 1
    LORA = 2  # unused
    GPS = 3


# it's hard to tell which device is plugged into the computer ... either on
# Raspian or on Mac.
#
# This class attempts to solve this by scanning the serial ports that appear to be
# candidates and then querying the interface to try to figure out what is what
class UsbDetector:

    __instance = None

    def __init__(self):
        self.usb_map: {UsbDevice, str} = {}
        self.device_map: {str, UsbDevice} = {}
        self.last_scan_time = 0

    @classmethod
    def init(cls):
        UsbDetector.__instance = UsbDetector()
        UsbDetector.__instance.__scan__()

    @classmethod
    def get_instance(cls):
        return UsbDetector.__instance

    @classmethod
    def get(cls, device_type: UsbDevice):
        return UsbDetector.__instance.usb_map[device_type]

    @classmethod
    def detected(cls, device_type: UsbDevice):
        return UsbDetector.__instance.usb_map.get(device_type) is not None

    def __scan__(self):
        devices = self.get_connected_serial_devices()
        logger.info(f"found usb serial devices : {devices}")

        # step 0 ... throw out already classified
        for device in devices:
            if os.path.getctime(device) < self.last_scan_time:
                logger.info(f"already mapped : {device}")
                devices.remove(device)

        # step 1 ... throw out the gps
        if devices:
            session = None
            try:
                session = gps()
                logger.info("gpsd is running")
                session.read()  # needed to get past version info
                session.send('?DEVICES;')
                code = session.read()
                if code == 0:
                    for gps_device in session.data['devices']:
                        device_path = gps_device['path']
                        self.usb_map[UsbDevice.GPS] = device_path
                        self.device_map[device_path] = UsbDevice.GPS
                        logger.info(f"associated {device_path} with GPS")
            except Exception as e:
                logger.error("didn't find connected GPS device", e)
            finally:
                if session:
                    session.close()

        # step 2 ..
        logger.info("detecting OBD devices")
        best_guess_obd_device = None
        for device in devices:
            if self.device_map.get(device):
                # it's been identified
                continue
            logger.info(f"trying to identify {device}")
            with serial.Serial(device, baudrate=38400, timeout=2) as ser:
                try:
                    ser.write("atz\r\r".encode("UTF-8"))
                    time.sleep(0.5)
                    resp_bytes = ser.readline(10)
                    logger.info(resp_bytes)
                    if "ELM" in str(resp_bytes):
                        self.usb_map[UsbDevice.OBD] = device
                        self.device_map[device] = UsbDevice.OBD
                        logger.info(f"associated {device} with OBD")
                except serial.SerialException:
                    pass
            best_guess_obd_device = device
        logger.info("finished USB scan")
        # if we've found GPS, but not found OBD but have a leftover USB device, try selecting it
        if UsbDevice.OBD not in self.usb_map and best_guess_obd_device is not None and UsbDevice.GPS in self.usb_map:
            logger.info(f"best guess is to use {best_guess_obd_device} as OBD device")
            self.usb_map[UsbDevice.OBD] = best_guess_obd_device
            self.device_map[best_guess_obd_device] = UsbDevice.OBD

        self.last_scan_time = time.time()

    @staticmethod
    def get_connected_serial_devices():
        os_type = platform.system()
        if os_type == "Linux":
            return glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        elif os_type == "Darwin":
            return glob.glob("/dev/tty.usbserial*")
        else:
            raise Exception("unknown platform: {}".format(os_type))


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    UsbDetector.init()
    print(UsbDetector.get_instance().usb_map)
