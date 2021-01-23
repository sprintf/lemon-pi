import logging

logger = logging.getLogger(__name__)

# a simple event framework so we can connect together decoupled logic
class EventHandler:

    def handle_event(self, event, **kwargs):
        pass


class Event:

    def __init__(self, name=""):
        self.name = name
        self.handlers = []

    def register_handler(self, handler:EventHandler):
        if handler not in self.handlers:
            self.handlers.append(handler)
        else:
            logger.error("{} attempted to register same handler twice {}", self.name, handler.__class__)

    def emit(self, **kwargs):
        logger.info("emitting {}".format(self.name))
        # call all the registered handlers
        for handler in self.handlers:
            handler.handle_event(self, **kwargs)


# emit() sends out
#   flag=
RaceStatusEvent = Event("race-flag")

# emit() sends out
#   car=
#   laps=
#   position=
#   ahead=   optional (only if someone ahead)
#   gap=     "-" if nobody ahead
LapCompletedEvent = Event("lap-completed")

# emit() sends out
#   car=
PittingEvent = Event("pitting")

# emit() sends out
#   car=
#   ts=
PingEvent = Event("ping")

# emit() sends out
#   car=
#   ts=
#   coolant_temp=
#   lap_count=
#   last_lap_time=
#   last_lap_fuel=
#   fuel_percent=
TelemetryEvent = Event("telemetry")