import unittest
from unittest.mock import MagicMock, patch
import time

from pit.events import RaceStatusEvent, LapCompletedEvent, PingEvent, PittingEvent, TelemetryEvent
from pit.radio_interface import RadioInterface
from shared.generated.messages_pb2 import Ping, EnteringPits, CarTelemetry


class RadioInterfaceTestCase(unittest.TestCase):

    @patch("shared.radio.Radio")
    def test_flags(self, radio):
        ri = RadioInterface(radio)
        for flag in ['Red', 'Green', 'Black', 'Yellow', '']:
            radio.send_async = MagicMock()
            ri.handle_event(RaceStatusEvent, flag=flag)
            radio.send_async.assert_called_once()

    @patch("shared.radio.Radio")
    def test_race_position(self, radio):
        ri = RadioInterface(radio)
        radio.send_async = MagicMock()
        ri.handle_event(LapCompletedEvent, car='1', laps=2, position=3)
        fields = radio.send_async.call_args.args[0]
        self.assertEqual("1", fields.car_number)
        self.assertEqual(2, fields.lap_count)
        self.assertEqual(3, fields.position)

    @patch("shared.radio.Radio")
    def test_race_position_behind(self, radio):
        ri = RadioInterface(radio)
        radio.send_async = MagicMock()
        ri.handle_event(LapCompletedEvent, car='1', laps=2, position=3, ahead="181", gap="5 laps")
        fields = radio.send_async.call_args.args[0]
        self.assertEqual("1", fields.car_number)
        self.assertEqual(2, fields.lap_count)
        self.assertEqual(3, fields.position)
        self.assertEqual("181", fields.car_ahead.car_number)
        self.assertEqual("5 laps", fields.car_ahead.gap_text)

    def test_ping_processing(self):
        ri = RadioInterface(MagicMock())
        handler = MagicMock()
        PingEvent.register_handler(handler)
        ping = Ping()
        ping.sender = "181"
        ping.timestamp = int(time.time())
        ri.convert_to_event(ping)
        handler.handle_event.assert_called_once_with(PingEvent, car=ping.sender, ts=ping.timestamp)

    def test_pitting_processing(self):
        ri = RadioInterface(MagicMock())
        handler = MagicMock()
        PittingEvent.register_handler(handler)
        pit = EnteringPits()
        pit.sender = "181"
        ri.convert_to_event(pit)
        handler.handle_event.assert_called_once_with(PittingEvent, car=pit.sender)

    def test_telemetry_processing(self):
        ri = RadioInterface(MagicMock())
        handler = MagicMock()
        TelemetryEvent.register_handler(handler)
        car = CarTelemetry()
        car.sender = "181"
        car.coolant_temp = 184
        car.lap_count = 50
        car.last_lap_time = 67.5
        car.last_lap_fuel_usage = 12
        car.fuel_remaining_percent = 25
        ri.convert_to_event(car)
        handler.handle_event.assert_called_once_with(TelemetryEvent,
                                                     car=car.sender,
                                                     ts=0,
                                                     coolant_temp=184,
                                                     lap_count=50,
                                                     last_lap_time=67.5,
                                                     last_lap_fuel=12,
                                                     fuel_percent=25)






if __name__ == '__main__':
    unittest.main()
