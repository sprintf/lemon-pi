import unittest
from unittest.mock import patch, Mock
import time

from lemon_pi.car.display_providers import TemperatureProvider, LapProvider, FuelProvider
from lemon_pi.car.event_defs import RadioSyncEvent
from lemon_pi.car.radio_interface import RadioInterface
from lemon_pi.shared.generated.messages_pb2 import SetFuelLevel, RaceStatus, RaceFlagStatus
from lemon_pi.shared.tests.lemon_pi_test_case import LemonPiTestCase


class RadioInterfaceTestCase(LemonPiTestCase):

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
