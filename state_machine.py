
from enum import Enum

from events import *


# define a few different states the car can be in at the track
class State(Enum):
    PARKED_IN_PIT = 1
    LEAVING_PIT = 2
    ON_TRACK = 3
    LEAVING_TRACK = 4


# this is the state machine that moves the car between the above states,
# based on the events in events.py
class StateMachine(EventHandler):

    def __init__(self):
        # todo : on power up determine if this is really whats going on
        # might break us if we get this wrong
        self.state = State.PARKED_IN_PIT
        # todo : register for all primary events (mustn't do all or we go into endless loop)
        MovingEvent.register_handler(self)
        CarStoppedEvent.register_handler(self)
        LeaveTrackEvent.register_handler(self)
        CompleteLapEvent.register_handler(self)

    def handle_event(self, event, speed=0, lat_long=None):
        # upon power on we assume we're in the pit, so this
        # isn't a completely reliable state
        if self.state == State.PARKED_IN_PIT:
            if event == MovingEvent:
                self.state = State.LEAVING_PIT
                StateChangeSettingOffEvent.emit()
                return
            # todo : toggle on obd tells us that we've refueled
            if event == OBDConnectedEvent:
                RefuelEvent.emit()
                return

        if self.state == State.ON_TRACK:
            if event == LeaveTrackEvent:
                self.state = State.LEAVING_TRACK
                # todo : emit a Pitting Message -> can send over radio
                return

        if self.state == State.LEAVING_TRACK:
            if event == CarStoppedEvent:
                self.state = State.PARKED_IN_PIT
                StateChangePittedEvent.emit()
                return

        if not self.state == State.ON_TRACK:
            if event == CompleteLapEvent:
                self.state = State.ON_TRACK
                return




