import unittest
from unittest.mock import patch, Mock

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


if __name__ == '__main__':
    unittest.main()
