
import numpy as np
import logging

from display_providers import FuelProvider
from updaters import MafUpdater, LapUpdater

logger = logging.getLogger(__name__)


class MafAnalyzer(MafUpdater, LapUpdater, FuelProvider):

    def __init__(self, lap_logger):
        self.lap_logger = lap_logger
        self.buffer_values = []
        self.total_fuel_used_ml = 0.0
        self.fuel_used_last_hour_ml = 0
        self.fuel_used_last_lap = 0.0
        self.fuel_used_this_lap = 0.0
        self.fuel_used_by_minute = []

    def update_lap(self, lap_count: int, last_lap_time: float):
        if lap_count > 0:
            self.fuel_used_last_lap = int(self.fuel_used_this_lap + self.__fuel_used_recent__())
            self.lap_logger.info("{},{:.2f},{}".format(lap_count, last_lap_time, self.fuel_used_last_lap))
        self.fuel_used_this_lap = 0.0
        pass

    def get_fuel_used_ml(self) -> int:
        return int(self.total_fuel_used_ml)

    def get_fuel_used_last_lap_ml(self) -> int:
        return int(self.fuel_used_last_lap)

    def get_fuel_used_last_hour_gallons(self) -> float:
        # todo : need to prevent recalculating this on every call
        # maintain a window of per minute sums
        # pull out the last 60 and sum them
        # sum last 60 elements in array
        if len(self.fuel_used_by_minute) == 0:
            return 0
        excess_elements = len(self.fuel_used_by_minute) - 60
        logger.debug("excess elements = {}".format(excess_elements))
        if excess_elements > 0:
            del self.fuel_used_by_minute[0:excess_elements]
        total_used = sum(self.fuel_used_by_minute)
        logger.debug("total used = {} ml".format(total_used))
        ml_per_hour = total_used * (60/len(self.fuel_used_by_minute))
        logger.debug("minutes = {}".format(len(self.fuel_used_by_minute)))
        # convert ml into US gallons
        total_gallons_used = ml_per_hour * 0.000264172
        logger.debug("estimated per hour = {} gph".format(ml_per_hour))
        return total_gallons_used

    def get_fuel_percent_remaining(self) -> int:
        if self.total_fuel_used_ml == 0:
            return -1
        # todo : set fuel full tank in settings somewhere
        # todo : upon reset functionality wipe out all history
        full_tank_ml = 66244
        return 100 - (int)((self.total_fuel_used_ml / full_tank_ml) * 100)

    # get a value in grams per second at a certain time
    def update_maf(self, value, time):
        # 10.8 to 1 is the IS300 air/fuel mix,
        # so we divide by 10.8 to get grams of fuel per second
        fuel_grams_per_second = value / 10.8
        # todo : weight a liter of '91 grade gas ... allegedly it weights about 750 grams
        ml_per_second = fuel_grams_per_second * (1000/750)
        self.buffer_values.append((ml_per_second, time))

        # print("adding {}".format(ml_per_second))
        # print("len values = {}".format(len(self.buffer_values)))
        # print(" time series length = {}".format(self.buffer_values[-1][1] - self.buffer_values[0][1]))

        # if we have a minute's worth of data, then accrue it
        if len(self.buffer_values) > 20 and \
            self.buffer_values[-1][1] - self.buffer_values[0][1] > 60:
            accumulated = self.__fuel_used_recent__()
            self.total_fuel_used_ml += accumulated
            self.fuel_used_this_lap += accumulated
            self.fuel_used_by_minute.append(accumulated)

            # create an array containing the last entry we had
            self.buffer_values = [self.buffer_values[-1]]

    # calculate the recent fuel used
    def __fuel_used_recent__(self) -> float:
        x_series = []
        y_series = []
        for (y, x) in self.buffer_values:
            x_series.append(x)
            y_series.append(y)
        result:np.float64 = np.trapz(y_series, x_series)
        print("recent fuel used = {} ml".format(result))
        return result



if __name__ == "__main__":
    buffer = [(0.6246913580246914, 1607925743.621162), (0.5950617283950618, 1607925743.97411), (0.5555555555555556, 1607925744.324518), (0.5419753086419753, 1607925744.678259), (0.5666666666666667, 1607925745.0313962), (0.5296296296296296, 1607925745.525534), (0.5049382716049382, 1607925745.8792498), (0.528395061728395, 1607925746.228811), (0.5333333333333333, 1607925746.5809531), (0.5444444444444444, 1607925746.929097), (0.5641975308641975, 1607925747.2791328), (0.5827160493827159, 1607925747.6322932), (0.5728395061728394, 1607925747.9829829), (0.5654320987654321, 1607925748.336693), (0.5913580246913579, 1607925748.686594), (0.5580246913580247, 1607925749.040107), (0.5580246913580247, 1607925749.393431), (0.5629629629629629, 1607925749.7435288), (0.5666666666666667, 1607925750.09631), (0.5629629629629629, 1607925750.446473)]
    x_series = []
    y_series = []
    for (y, x) in buffer:
        x_series.append(x)
        y_series.append(y)
    dy = np.trapz(y_series, x_series)
    print(dy)
    print(np.trapz(y_series))
    # pd.Series()

#  next try with pandas time series


