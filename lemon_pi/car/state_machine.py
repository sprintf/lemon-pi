
from enum import Enum

from lemon_pi.car.event_defs import *


# define a few different states the car can be in at the track
from lemon_pi.shared.events import EventHandler


class State(Enum):
    PARKED_IN_PIT = 1
    LEAVING_PIT = 2
    ON_TRACK = 3
    LEAVING_TRACK = 4


# this is the state machine that moves the car between the above states,
# based on the events in events.py
class StateMachine(EventHandler):

    __instance = None

    def __init__(self):
        # we assume we're parked in pit when we are initialized, if we're not
        # we're in big trouble anyway. If we cross the start-finish line then we
        # switch state to ON_TRACK anyway
        self.state = State.PARKED_IN_PIT
        MovingEvent.register_handler(self)
        CarStoppedEvent.register_handler(self)
        LeaveTrackEvent.register_handler(self)
        CompleteLapEvent.register_handler(self)
        OBDConnectedEvent.register_handler(self)

    @classmethod
    def init(cls):
        StateMachine.__instance = StateMachine()

    @classmethod
    def is_on_track(cls):
        return StateMachine.__instance.state == State.ON_TRACK

    def handle_event(self, event, **kwargs):
        # upon power on we assume we're in the pit, so this
        # isn't a completely reliable state
        if self.state == State.PARKED_IN_PIT:
            if event == MovingEvent:
                self.state = State.LEAVING_PIT
                StateChangeSettingOffEvent.emit()
                return
            if event == OBDConnectedEvent:
                RefuelEvent.emit(percent_full=100)
                return

        if self.state == State.ON_TRACK:
            if event == LeaveTrackEvent:
                self.state = State.LEAVING_TRACK
                return

        if self.state in [State.LEAVING_TRACK, State.LEAVING_PIT]:
            if event == CarStoppedEvent:
                self.state = State.PARKED_IN_PIT
                StateChangePittedEvent.emit()
                return

        if not self.state == State.ON_TRACK:
            if event == CompleteLapEvent:
                self.state = State.ON_TRACK
                return




