
import numpy as np
import logging
import time
from python_settings import settings


from lemon_pi.car.display_providers import FuelProvider
from lemon_pi.car.event_defs import RefuelEvent
from lemon_pi.car.updaters import FuelUsageUpdater, LapUpdater
from lemon_pi.shared.events import EventHandler

logger = logging.getLogger(__name__)


class MafAnalyzer(FuelUsageUpdater, LapUpdater, FuelProvider, EventHandler):

    def __init__(self, lap_logger):
        self.lap_logger = lap_logger
        self.buffer_values = []
        self.total_fuel_used_ml = 0.0
        self.fuel_used_last_hour_ml = 0
        self.fuel_used_last_lap = 0.0
        self.fuel_used_this_lap = 0.0
        self.fuel_used_by_minute = []
        self.cached_fuel_usage = None
        self.cached_fuel_usage_time = 0.0
        RefuelEvent.register_handler(self)

    def handle_event(self, event, percent_full=100, **kwargs):
        logger.info("refuelling")
        self.set_fuel_percent_remaining(percent_full)

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

    def get_fuel_used_last_hour_ml(self) -> int:
        # return a known good value
        if time.time() - self.cached_fuel_usage_time < 60:
            return self.cached_fuel_usage

        # we maintain a window of per minute fuel consumption
        # here we pull out the last 60 and sum them
        if len(self.fuel_used_by_minute) == 0:
            return 0

        # trim the excess data, if necessary
        excess_elements = len(self.fuel_used_by_minute) - 60
        logger.debug("excess elements = {}".format(excess_elements))
        if excess_elements > 0:
            del self.fuel_used_by_minute[0:excess_elements]

        total_used = sum(self.fuel_used_by_minute)
        logger.debug("total used = {} ml".format(total_used))
        ml_per_hour = total_used * (60/len(self.fuel_used_by_minute))
        logger.debug("minutes = {}".format(len(self.fuel_used_by_minute)))
        self.cached_fuel_usage = ml_per_hour
        self.cached_fuel_usage_time = time.time()
        return ml_per_hour

    def get_fuel_percent_remaining(self) -> int:
        full_tank_ml = self._get_full_tank_ml()
        return 100 - int((self.total_fuel_used_ml / full_tank_ml) * 100)

    def set_fuel_percent_remaining(self, percent_remaining):
        full_tank_ml = self._get_full_tank_ml()
        self.total_fuel_used_ml = (100 - percent_remaining) * (full_tank_ml / 100)
        self.buffer_values = []

    def _get_full_tank_ml(self) -> int:
        # there's 3785 millilitres in a gallon
        return int(settings.FUEL_CAPACITY_US_GALLONS * 3785)

    # get a value in grams per second at a certain time
    def update_fuel(self, ml_per_second:float, time:float):
        self.buffer_values.append((ml_per_second, time))

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


