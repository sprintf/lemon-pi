import unittest
from unittest.mock import patch, Mock

from lemon_pi.car.event_defs import EnterTrackEvent, LeaveTrackEvent
from lemon_pi.car.radio_interface import RadioInterface
from lemon_pi_pb2 import SetFuelLevel, RaceStatus, SetTargetTime, ResetFastLap, ToPitMessage
from race_flag_status_pb2 import RaceFlagStatus
from lemon_pi.shared.tests.lemon_pi_test_case import LemonPiTestCase


class RadioInterfaceTestCase(LemonPiTestCase):

    @patch("lemon_pi.shared.meringue_comms.MeringueComms.send_message_from_car")
    def test_entering_track(self, grpc_call):
        comms = Mock()
        comms.send_message_from_car = grpc_call
        ri = RadioInterface(comms, None, None, None)
        EnterTrackEvent.emit()
        msg = ToPitMessage()
        msg.entering.timestamp = 1
        grpc_call.assert_called_with(msg)

    @patch("lemon_pi.shared.meringue_comms.MeringueComms.send_message_from_car")
    def test_leaving_track(self, grpc_call):
        comms = Mock()
        comms.send_message_from_car = grpc_call
        ri = RadioInterface(comms, None, None, None)
        LeaveTrackEvent.emit()
        msg = ToPitMessage()
        msg.pitting.timestamp = 1
        grpc_call.assert_called_with(msg)

    @patch("lemon_pi.car.event_defs.RaceFlagStatusEvent.emit")
    def test_unknown_flag(self, race_status_event):
        ri = RadioInterface(Mock(), None, None, None)
        ri.process_incoming(RaceStatus())
        race_status_event.assert_called_with(flag='UNKNOWN')

    @patch("lemon_pi.car.event_defs.DriverMessageEvent.emit")
    @patch("lemon_pi.car.event_defs.RaceFlagStatusEvent.emit")
    def test_red_flag(self, race_status_event, driver_message_event):
        ri = RadioInterface(Mock(), None, None, None)
        red_flag = RaceStatus()
        red_flag.flag_status = RaceFlagStatus.RED
        ri.process_incoming(red_flag)
        race_status_event.assert_called_with(flag='RED')
        driver_message_event.assert_called_with(text='Race Red Flagged', duration_secs=10)

    @patch("lemon_pi.car.event_defs.RefuelEvent.emit")
    def test_refuel_message(self, refuel_event):
        ri = RadioInterface(Mock(), None, None, None)
        fuel_level = SetFuelLevel()
        # this matches what is in test-settings
        fuel_level.car_number = "999"
        ri.process_incoming(fuel_level)
        refuel_event.assert_called_with(percent_full=100)

    @patch("lemon_pi.car.event_defs.RefuelEvent.emit")
    def test_refuel_message_with_percent(self, refuel_event):
        ri = RadioInterface(Mock(), None, None, None)
        sf = SetFuelLevel()
        sf.percent_full = 69
        sf.car_number = "999"
        ri.process_incoming(sf)
        refuel_event.assert_called_with(percent_full=69)

    @patch("lemon_pi.car.event_defs.SetTargetTimeEvent.emit")
    def test_zero_target_time_message(self, target_time_event):
        ri = RadioInterface(Mock(), None, None, None)
        target_message = SetTargetTime()
        target_message.car_number = "999"
        target_message.target_lap_time = 0.0
        ri.process_incoming(target_message)
        target_time_event.assert_called_with(target=0.0)

    @patch("lemon_pi.car.event_defs.SetTargetTimeEvent.emit")
    def test_non_zero_target_time_message(self, target_time_event):
        ri = RadioInterface(Mock(), None, None, None)
        target_message = SetTargetTime()
        target_message.car_number = "999"
        target_message.target_lap_time = 128.5
        ri.process_incoming(target_message)
        target_time_event.assert_called_with(target=128.5)

    @patch("lemon_pi.car.event_defs.ResetFastLapEvent.emit")
    def test_reset_fast_lap_message(self, reset_fast_lap_event):
        ri = RadioInterface(Mock(), None, None, None)
        target_message = ResetFastLap()
        target_message.car_number = "999"
        ri.process_incoming(target_message)
        reset_fast_lap_event.assert_called_once()

if __name__ == '__main__':
    unittest.main()
