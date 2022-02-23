
import subprocess
import platform
import time
import logging
import os
from threading import Thread

from python_settings import settings

from lemon_pi.car.event_defs import WifiConnectedEvent, WifiDisconnectedEvent

logger = logging.getLogger(__name__)


class WifiManager:

    wifi_connected: bool = False

    @classmethod
    def _get_wifi_command(cls):
        sys = platform.system()
        if sys == "Linux":
            return ['ifconfig', 'wlan0']
        elif sys == "Darwin":
            return ['ifconfig', 'en0']
        else:
            raise Exception("unknown platform")

    @classmethod
    def monitor_wifi(cls):
        Thread(target=WifiManager.check_wifi_repeatedly, daemon=True).start()

    @classmethod
    def check_wifi_repeatedly(cls):
        while True:
            WifiManager.check_wifi_enabled()
            time.sleep(5)

    @classmethod
    def check_wifi_enabled(cls):
        response = WifiManager._command(WifiManager._get_wifi_command())
        if "RUNNING" in response and "inet " in response:
            if not WifiManager.wifi_connected:
                logger.info("wifi operating")
                WifiManager.wifi_connected = True
                WifiConnectedEvent.emit()
            return True
        else:
            if WifiManager.wifi_connected:
                logger.info("wifi is disconnected")
                WifiManager.wifi_connected = False
                WifiDisconnectedEvent.emit()
        return False

    @classmethod
    def disable_wifi(cls):
        if platform.system() == "Linux":
            WifiManager._command(['sudo', 'rfkill', 'block', 'wifi'])
            logger.info("wifi disabled")

    @classmethod
    def enable_wifi(cls):
        if platform.system() == "Linux":
            # if there's a particular wifi in settings then make sure we're configured
            needs_writing = False
            if settings.WIFI_SSID:
                with open('/etc/wpa_supplicant/wpa_supplicant.conf') as wifi_config_file:
                    whole_file = wifi_config_file.read()
                    if settings.WIFI_SSID not in whole_file or settings.WIFI_PASSWORD not in whole_file:
                        needs_writing = True
                if needs_writing:
                    WifiManager._write_wifi_config_file(settings.WIFI_SSID, settings.WIFI_PASSWORD)

            WifiManager._command(['sudo', 'rfkill', 'unblock', 'wifi'])
            logger.info("waiting for wifi to enable...")
            time.sleep(10)
            logger.info("that's enough waiting")
            WifiManager.check_wifi_enabled()

    @classmethod
    def _write_wifi_config_file(cls, ssid, password):
        with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'a') as wifi_config_file:
            network_setting = """
network={{
    ssid="{0}"
    psk="{1}"
}}
""".format(ssid, password)
            wifi_config_file.write(network_setting)

    @classmethod
    def _command(cls, args):
        result = subprocess.run(args, stdout=subprocess.PIPE)
        return result.stdout.decode("UTF-8").strip()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    if "SETTINGS_MODULE" not in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_car"

    WifiManager._write_wifi_config_file(settings.WIFI_SSID, settings.WIFI_PASSWORD)
