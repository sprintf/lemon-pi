
from pit.datasource.datasource_handler import DataSourceHandler
from pit.leaderboard import RaceOrder
from datetime import datetime
import time

# Utility that can play through a recorded file of a race, at a faster simulated speed

def sim_race(file, handler:DataSourceHandler, time_factor=1):
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
            print(line)



if __name__ == "__main__":
    leaderboard = RaceOrder()
    handler = DataSourceHandler(leaderboard, "156")
    sim_race("../resources/test/test-file.dat", handler, time_factor=100)