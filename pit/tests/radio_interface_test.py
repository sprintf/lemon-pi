import unittest
from unittest.mock import MagicMock, patch

from pit.events import RaceStatusEvent, LapCompletedEvent
from pit.radio_interface import RadioInterface


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


if __name__ == '__main__':
    unittest.main()
