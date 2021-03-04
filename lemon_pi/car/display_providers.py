
import datetime

# a mixin for things that are flakey ...
# particularly GPS
class UnreliableProviderMixin:

    def is_working(self) -> bool:
        pass


class TemperatureProvider(UnreliableProviderMixin):

    def get_temp_f(self) -> int:
        pass


class SpeedProvider(UnreliableProviderMixin):

    def get_speed(self) -> int:
        pass

    def get_heading(self) -> int:
        pass


class PositionProvider(UnreliableProviderMixin):

    def get_lat_long(self) -> (float, float):
        pass


class LapProvider():

    # get the lap count
    def get_lap_count(self) -> int:
        pass

    # return seconds since start of lap
    def get_lap_timer(self) -> int:
        pass

    # return seconds and millis for last lap
    def get_last_lap_time(self) -> float:
        pass


class FuelProvider:

    def get_fuel_used_ml(self) -> int:
        pass

    def get_fuel_used_last_lap_ml(self) -> int:
        pass

    def get_fuel_used_last_hour_ml(self) -> int:
        pass

    def get_fuel_percent_remaining(self) -> int:
        pass

