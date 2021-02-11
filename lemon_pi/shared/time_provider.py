
import datetime


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