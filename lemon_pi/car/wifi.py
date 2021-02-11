
import subprocess
import platform


class WifiManager:

    def check_wifi(self):
        if platform.system() == "Linux":
            response = self.command(['ifconfig', 'wlan0'])
            if response.find("RUNNING") and response.find("inet "):
                return True
        return False

    def disable_wifi(self):
        if platform.system() == "Linux":
            self.command(['sudo', 'rfkill', 'block', 'wifi'])


    def command(self, args):
        result = subprocess.run(args, stdout=subprocess.PIPE)
        return result.stdout.decode("UTF-8").strip()

