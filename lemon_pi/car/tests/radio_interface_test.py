import unittest
from unittest.mock import patch, Mock
import time

from lemon_pi.car.display_providers import TemperatureProvider, LapProvider, FuelProvider
from lemon_pi.car.event_defs import RadioSyncEvent
from lemon_pi.car.radio_interface import RadioInterface
from lemon_pi.shared.generated.messages_pb2 import SetFuelLevel
from lemon_pi.shared.tests.lemon_pi_test_case import LemonPiTestCase


class RadioInterfaceTestCase(LemonPiTestCase):

    @patch("lemon_pi.car.event_defs.RefuelEvent.emit")
    def test_refuel_message(self, refuel_event):
        ri = RadioInterface(Mock(), None, None, None)
        ri.process_incoming(SetFuelLevel())
        refuel_event.assert_called_with(percent_full=100)

    @patch("lemon_pi.car.event_defs.RefuelEvent.emit")
    def test_refuel_message_with_percent(self, refuel_event):
        ri = RadioInterface(Mock(), None, None, None)
        sf = SetFuelLevel()
        sf.percent_full = 69
        ri.process_incoming(sf)
        refuel_event.assert_called_with(percent_full=69)

    def test_handling_radio_sync(self):
        temp_provider = TemperatureProvider()
        temp_provider.get_temp_f = Mock(return_value=188)
        lap_provider = LapProvider()
        lap_provider.get_last_lap_time = Mock(return_value=120.1)
        lap_provider.get_lap_count = Mock(return_value=15)
        fuel_provider = FuelProvider()
        fuel_provider.get_fuel_used_last_lap_ml = Mock(return_value=223)
        fuel_provider.get_fuel_percent_remaining = Mock(return_value=31)

        radio = Mock()
        radio.send_async = Mock()
        ri = RadioInterface(radio, temp_provider, lap_provider, fuel_provider)
        RadioSyncEvent.emit(ts=time.time())
        radio.send_async.assert_called_once()

if __name__ == '__main__':
    unittest.main()
