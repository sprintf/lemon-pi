import unittest
from unittest.mock import MagicMock, patch
import time

from lemon_pi.pit.event_defs import RaceStatusEvent, LapCompletedEvent, PingEvent, PittingEvent, TelemetryEvent, \
    SendTargetTimeEvent
from lemon_pi.pit.radio_interface import RadioInterface
from lemon_pi_pb2 import Ping, EnteringPits, CarTelemetry, ToCarMessage, RaceStatus, RacePosition
from race_flag_status_pb2 import RaceFlagStatus
from python_settings import settings
import lemon_pi.config.test_settings as my_local_settings
from lemon_pi.shared.tests.lemon_pi_test_case import LemonPiTestCase

if not settings.configured:
    settings.configure(my_local_settings)

class RadioInterfaceTestCase(LemonPiTestCase):

    @patch("lemon_pi.pit.meringue_comms_pit.MeringueCommsPitsReader")
    @patch("lemon_pi.shared.radio.Radio")
    def test_flags(self, radio, comms):
        ri = RadioInterface(radio, comms)
        for flag in ['Red', 'Green', 'Black', 'Yellow', '']:
            radio.send_async = MagicMock()
            comms.send_message_to_car = MagicMock()
            ri.handle_event(RaceStatusEvent, flag=flag)
            radio.send_async.assert_called_once()

    @patch("lemon_pi.pit.meringue_comms_pit.MeringueCommsPitsReader")
    @patch("lemon_pi.shared.radio.Radio")
    def test_race_position(self, radio, comms):
        ri = RadioInterface(radio, comms)
        radio.send_async = MagicMock()
        comms.send_message_to_car = MagicMock()
        ri.handle_event(LapCompletedEvent, car='1', laps=2, position=3)
        expected = ToCarMessage()
        expected.race_position.car_number = "1"
        expected.race_position.lap_count = 2
        expected.race_position.position = 3
        radio.send_async.assert_called_once_with(expected)
        comms.send_message_to_car.assert_called_once_with(expected)

    @patch("lemon_pi.pit.meringue_comms_pit.MeringueCommsPitsReader")
    @patch("lemon_pi.shared.radio.Radio")
    def test_race_position_behind(self, radio, comms):
        ri = RadioInterface(radio, comms)
        radio.send_async = MagicMock()
        comms.send_message_to_car = MagicMock()
        ri.handle_event(LapCompletedEvent, car='1', laps=2, position=3, ahead="181", gap="5 laps")
        expected = ToCarMessage()
        expected.race_position.car_number = "1"
        expected.race_position.lap_count = 2
        expected.race_position.position = 3
        expected.race_position.car_ahead.car_number = "181"
        expected.race_position.car_ahead.gap_text = "5 laps"
        radio.send_async.assert_called_once_with(expected)
        comms.send_message_to_car.assert_called_once_with(expected)

    @patch("lemon_pi.pit.meringue_comms_pit.MeringueCommsPitsReader")
    @patch("lemon_pi.shared.radio.Radio")
    def test_race_position_with_flag(self, radio, comms):
        ri = RadioInterface(radio, comms)
        radio.send_async = MagicMock()
        comms.send_message_to_car = MagicMock()
        ri.handle_event(LapCompletedEvent, car='1', laps=2, position=3, ahead="181", flag="Green")
        expected = ToCarMessage()
        expected.race_position.car_number = "1"
        expected.race_position.lap_count = 2
        expected.race_position.position = 3
        expected.race_position.car_ahead.car_number = "181"
        expected.race_position.flag_status = RaceFlagStatus.GREEN
        radio.send_async.assert_called_once_with(expected)
        comms.send_message_to_car.assert_called_once_with(expected)

    @patch("lemon_pi.pit.meringue_comms_pit.MeringueCommsPitsReader")
    @patch("lemon_pi.shared.radio.Radio")
    def test_target_time_int(self, radio, comms):
        ri = RadioInterface(radio, comms)
        radio.send_async = MagicMock()
        comms.send_message_to_car = MagicMock()
        ri.handle_event(SendTargetTimeEvent, car='1', target_time=0)
        expected = ToCarMessage()
        expected.set_target.car_number = "1"
        expected.set_target.target_lap_time = 0.0
        radio.send_async.assert_called_once_with(expected)
        comms.send_message_to_car.assert_called_once_with(expected)

    @patch("lemon_pi.pit.meringue_comms_pit.MeringueCommsPitsReader")
    @patch("lemon_pi.shared.radio.Radio")
    def test_target_time_float(self, radio, comms):
        ri = RadioInterface(radio, comms)
        radio.send_async = MagicMock()
        comms.send_message_to_car = MagicMock()
        ri.handle_event(SendTargetTimeEvent, car='1', target_time=128.5)
        expected = ToCarMessage()
        expected.set_target.car_number = "1"
        expected.set_target.target_lap_time = 128.5
        radio.send_async.assert_called_once_with(expected)
        comms.send_message_to_car.assert_called_once_with(expected)

    def test_ping_processing(self):
        ri = RadioInterface(MagicMock(), MagicMock())
        handler = MagicMock()
        PingEvent.register_handler(handler)
        ping = Ping()
        ping.sender = "181"
        ping.timestamp = int(time.time())
        ri.convert_to_event(ping)
        handler.handle_event.assert_called_once_with(PingEvent, car=ping.sender, ts=ping.timestamp)

    def test_pitting_processing(self):
        ri = RadioInterface(MagicMock(), MagicMock())
        handler = MagicMock()
        PittingEvent.register_handler(handler)
        pit = EnteringPits()
        pit.sender = "181"
        ri.convert_to_event(pit)
        handler.handle_event.assert_called_once_with(PittingEvent, car=pit.sender)

    def test_race_status_processing(self):
        ri = RadioInterface(MagicMock(), MagicMock())
        handler = MagicMock()
        RaceStatusEvent.register_handler(handler)
        status = RaceStatus()
        status.flag_status = RaceFlagStatus.GREEN
        ri.convert_to_event(status)
        handler.handle_event.assert_called_once_with(RaceStatusEvent, flag="GREEN")

    def test_lap_completed(self):
        ri = RadioInterface(MagicMock(), MagicMock())
        handler = MagicMock()
        LapCompletedEvent.register_handler(handler)
        status = RacePosition()
        status.sender = "meringue"
        status.car_number = "181"
        status.position = 2
        status.position_in_class = 1
        status.lap_count= 99
        status.last_lap_time = 122.5
        status.car_ahead.car_number= "183"
        status.car_ahead.gap_text = "3 laps"
        ri.convert_to_event(status)
        handler.handle_event.assert_called_once_with(LapCompletedEvent,
                                                     car="181",
                                                     position=2,
                                                     class_position=1,
                                                     gap='3 laps',
                                                     laps=99,
                                                     last_lap_time=122.5)

    def test_telemetry_processing(self):
        ri = RadioInterface(MagicMock(), MagicMock())
        handler = MagicMock()
        TelemetryEvent.register_handler(handler)
        car = CarTelemetry()
        car.sender = "181"
        car.coolant_temp = 184
        car.lap_count = 50
        car.last_lap_time = 67.5
        car.fuel_remaining_percent = 25
        ri.convert_to_event(car)
        handler.handle_event.assert_called_once_with(TelemetryEvent,
                                                     car=car.sender,
                                                     ts=0,
                                                     coolant_temp=184,
                                                     lap_count=50,
                                                     last_lap_time=67.5,
                                                     fuel_percent=25)






if __name__ == '__main__':
    unittest.main()
