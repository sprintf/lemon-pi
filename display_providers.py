
import datetime

# a mixin for things that are flakey ...
# particularly GPS
class UnreliableProviderMixin:

    def is_working(self) -> bool:
        pass


class TemperatureProvider(UnreliableProviderMixin):

    def get_temp_f(self) -> int:
        pass


class TimeProvider:

    def get_hours(self) -> int:
        pass

    def get_minutes(self) -> int:
        pass

    def get_seconds(self) -> int:
        pass


class LocalTimeProvider(TimeProvider):

    def get_hours(self) -> int:
        hour = datetime.datetime.now().hour
        return hour if hour < 13 else hour - 12

    def get_minutes(self) -> int:
        return datetime.datetime.now().minute

    def get_seconds(self) -> int:
        return datetime.datetime.now().second


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

    def get_last_lap_time(self) -> int:
        pass


class FuelProvider:

    # fuel used in milliliters
    # there's 66244 millilitres in 17.5 gallons
    def get_fuel_used_ml(self) -> int:
        pass

    def get_fuel_used_last_lap_ml(self) -> int:
        pass

    def get_fuel_used_last_hour_gallons(self) -> float:
        pass

    def get_fuel_percent_remaining(self) -> int:
        pass

