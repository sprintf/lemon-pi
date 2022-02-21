
import subprocess
import platform
import time
import logging
import os
from python_settings import settings

from lemon_pi.car.event_defs import WifiConnectedEvent, WifiDisconnectedEvent

logger = logging.getLogger(__name__)



class WifiManager:

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
    def check_wifi_enabled(cls):
        logger.info("detecting wifi...")
        response = WifiManager._command(WifiManager._get_wifi_command())
        if "RUNNING" in response and "inet " in response:
            logger.info("wifi operating")
            WifiConnectedEvent.emit()
            return True
        else:
            logger.info("wifi is disabled")
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
                    if not settings.WIFI_SSID in whole_file or not settings.WIFI_PASSWORD in whole_file:
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
network={
    ssid="%s"
    psk="%s"
}
""".format(ssid, password)
            wifi_config_file.write(network_setting)


    @classmethod
    def _command(cls, args:[]):
        result = subprocess.run(args, stdout=subprocess.PIPE)
        return result.stdout.decode("UTF-8").strip()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    if not "SETTINGS_MODULE" in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_pit"

    WifiManager._write_wifi_config_file(settings.WIFI_SSID, settings.WIFI_PASSWORD)

