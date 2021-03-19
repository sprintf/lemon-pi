import os
import logging
from threading import Thread

from lemon_pi.pit.datasource.datasource_handler import DataSourceHandler
from lemon_pi.pit.gui import Gui
from lemon_pi.pit.leaderboard import RaceOrder, PositionEnum
from datetime import datetime
from python_settings import settings
import time

# Utility that can play through a recorded file of a race, at a faster simulated speed
from lemon_pi.pit.radio_interface import RadioInterface
from lemon_pi.pit.strategy_analyzer import StrategyAnalyzer
from lemon_pi.shared.generated.messages_pb2 import ToPitMessage
from lemon_pi.shared.radio import Radio
from lemon_pi.shared.usb_detector import UsbDetector

logger = logging.getLogger(__name__)

logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

def sim_race(file, handler:DataSourceHandler, time_factor):
    simtime = 0

    with open(file) as f:
        for line in f.readlines():
            handler.handle_message(line)
            l = line.strip()
            if l.startswith("$"):
                bits = l.split(",")
                if bits[0] == "$RMCA" and len(bits) == 2:
                    print("time = {}".format(int(bits[1]) / 1000))
                    simtime = datetime.fromtimestamp(int(bits[1]) / 1000)
                    nowtime = datetime.now()
                    difftime = nowtime - simtime
                    print("time diff = {} which is {}s".format(difftime, difftime.total_seconds()))
                    timeshift = int(difftime.total_seconds())
                if bits[0] == "$RMLT" and len(bits) == 3:
                    linetime = datetime.fromtimestamp(int(bits[2]) / 1000)
                    gap = linetime - simtime
                    if gap.total_seconds() > 0:
                        print("for {} gap is {} ... sleeping".format(bits[1], gap))
                        time.sleep(gap.total_seconds() / time_factor)
                        simtime = linetime
                # if bits[0] == "$COMP" and len(bits) == 8:
                #     print("adding {}")
            #print(line)

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_pit"


def run_sim(gui, leaderboard, car_number):
    gui.progress(100)
    handler = DataSourceHandler(leaderboard, car_number)
    sim_race("../../resources/test/test-file.dat", handler, 5)


if __name__ == "__main__":
    UsbDetector().init()

    radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY, ToPitMessage())
    radio.start()

    time.sleep(3)

    ri = RadioInterface(radio)
    ri.start()

    leaderboard = RaceOrder()

    car_number = "909"
    sa = StrategyAnalyzer(leaderboard, car_number)
    sa.set_position_mode(PositionEnum.IN_CLASS)
    sa.start()

    gui = Gui()
    gui.set_target_car(car_number)
    Thread(target=run_sim, args=[gui, leaderboard, car_number], daemon=True).start()
    gui.display()
