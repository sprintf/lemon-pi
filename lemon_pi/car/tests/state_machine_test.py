import unittest
from unittest.mock import Mock, patch
import time


from lemon_pi.car.event_defs import (
    MovingEvent,
    LeaveTrackEvent, CompleteLapEvent, CarStoppedEvent, OBDConnectedEvent
)
from lemon_pi.car.state_machine import (
    StateMachine,
    State
)
from lemon_pi.shared.tests.lemon_pi_test_case import LemonPiTestCase


class StateMachineTestCase(LemonPiTestCase):

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
        # force 10s to pass
        CarStoppedEvent.last_event_time = time.time() - 11
        CarStoppedEvent.emit()
        self.assertEqual(sm.state, State.PARKED_IN_PIT)

    @patch("lemon_pi.car.event_defs.RefuelEvent.emit")
    def test_obd_reconnecting_in_pit_issues_refuel(self, refuel_event):
        sm = StateMachine()
        CarStoppedEvent.emit()
        self.assertEqual(sm.state, State.PARKED_IN_PIT)
        refuel_event.assert_not_called()
        OBDConnectedEvent.emit()
        refuel_event.assert_called()



if __name__ == '__main__':
    unittest.main()
