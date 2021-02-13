import unittest
from unittest.mock import Mock

from lemon_pi.car.event_defs import (
    MovingEvent,
    LeaveTrackEvent, CompleteLapEvent, CarStoppedEvent, RefuelEvent, OBDConnectedEvent
)
from lemon_pi.car.state_machine import (
    StateMachine,
    State
)


class StateMachineTestCase(unittest.TestCase):

    def test_initial_state(self):
        sm = StateMachine()
        self.assertEqual(sm.state, State.PARKED_IN_PIT)

    def test_false_pit_detection(self):
        sm = StateMachine()
        MovingEvent.emit()
        LeaveTrackEvent.emit()
        CompleteLapEvent.emit()
        self.assertEqual(sm.state, State.ON_TRACK)

    def test_pitting(self):
        sm = StateMachine()
        sm.state = State.ON_TRACK
        MovingEvent.emit()
        LeaveTrackEvent.emit()
        self.assertEqual(sm.state, State.LEAVING_TRACK)
        CarStoppedEvent.emit()
        self.assertEqual(sm.state, State.PARKED_IN_PIT)
        # then suppose we move and are then stationary again
        MovingEvent.emit()
        self.assertEqual(sm.state, State.LEAVING_PIT)
        CarStoppedEvent.emit()
        self.assertEqual(sm.state, State.PARKED_IN_PIT)

    def test_obd_reconnecting_in_pit_issues_refuel(self):
        sm = StateMachine()
        CarStoppedEvent.emit()
        self.assertEqual(sm.state, State.PARKED_IN_PIT)
        RefuelEvent.emit = Mock()
        OBDConnectedEvent.emit()
        RefuelEvent.emit.assert_called_once()



if __name__ == '__main__':
    unittest.main()
