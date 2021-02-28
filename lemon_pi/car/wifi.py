
import subprocess
import platform
import time


class WifiManager:

    @classmethod
    def check_wifi_enabled(self):
        if platform.system() == "Linux":
            response = WifiManager._command(['ifconfig', 'wlan0'])
            if response.find("RUNNING") and response.find("inet "):
                return True
        return False

    @classmethod
    def disable_wifi(self):
        if platform.system() == "Linux":
            WifiManager._command(['sudo', 'rfkill', 'block', 'wifi'])

    @classmethod
    def enable_wifi(self):
        if platform.system() == "Linux":
            WifiManager._command(['sudo', 'rfkill', 'unblock', 'wifi'])
            time.sleep(3)

    @classmethod
    def _command(self, args:[]):
        result = subprocess.run(args, stdout=subprocess.PIPE)
        return result.stdout.decode("UTF-8").strip()

