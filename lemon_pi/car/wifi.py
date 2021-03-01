
import subprocess
import platform
import time
import logging

logger = logging.getLogger(__name__)


class WifiManager:

    @classmethod
    def check_wifi_enabled(cls):
        if platform.system() == "Linux":
            logger.info("detecting wifi...")
            response = WifiManager._command(['ifconfig', 'wlan0'])
            if "RUNNING" in response and "inet " in response:
                logger.info("wifi operating")
                return True
            else:
                logger.info("wifi is disabled")
        return False

    @classmethod
    def disable_wifi(cls):
        if platform.system() == "Linux":
            WifiManager._command(['sudo', 'rfkill', 'block', 'wifi'])
            logger.info("wifi disabled")

    @classmethod
    def enable_wifi(cls):
        if platform.system() == "Linux":
            WifiManager._command(['sudo', 'rfkill', 'unblock', 'wifi'])
            logger.info("waiting for wifi to enable...")
            time.sleep(7)
            logger.info("that's enough waiting")

    @classmethod
    def _command(cls, args:[]):
        result = subprocess.run(args, stdout=subprocess.PIPE)
        return result.stdout.decode("UTF-8").strip()

