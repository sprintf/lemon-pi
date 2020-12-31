
import logging

logger = logging.getLogger(__name__)

# a simple event framework so we can connect together decoupled logic
class EventHandler:

    def handle_event(self, event, **kwargs):
        pass


class Event:

    # stop the logs getting too full : suppress repeat events in info log
    last_event = None
    last_event_count = 0

    def __init__(self, name=""):
        self.name = name
        self.handlers = []

    def register_handler(self, handler:EventHandler):
        if handler not in self.handlers:
            self.handlers.append(handler)
        else:
            logger.error("{} attempted to register same handler twice {}", self.name, handler.__class__)

    def emit(self, **kwargs):
        if self == Event.last_event:
            Event.last_event_count += 1
        else:
            if Event.last_event_count > 0:
                logger.info("suppressed ({}) {}".format(Event.last_event_count, Event.last_event.name))
            logger.info("emitting {}".format(self.name))
            Event.last_event_count = 0
        Event.last_event = self
        # call all the registered handlers
        for handler in self.handlers:
            handler.handle_event(self, **kwargs)


# the car is moving
MovingEvent = Event("Moving")

# the car is not moving
NotMovingEvent = Event("NotMoving")

# the car is exiting the race track and entering the pits
LeaveTrackEvent = Event("LeaveTrack")

# a lap has been completed
CompleteLapEvent = Event("CompleteLap")

# a request to exit the application
ExitApplicationEvent = Event("ExitApplication")

### State Change Events

# the car is setting off from pits
StateChangeSettingOffEvent = Event("StateChangeSettingOff")

# the car is parked in the pits
StateChangePittedEvent = Event("StateChangePitted")

### OBD connected
OBDConnectedEvent = Event("OBD-Connected")

### OBD disconnected
OBDDisconnectedEvent = Event("OBD-Disconnected")

### Refuel event
RefuelEvent = Event("Refuel")

### Car has come to a halt
CarStoppedEvent = Event("CarStopped")



