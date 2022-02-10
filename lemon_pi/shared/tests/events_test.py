import unittest
from unittest.mock import Mock

from lemon_pi.shared.events import Event

TestEvent = Event("test")

class EventsTestCase(unittest.TestCase):

    def test_register_deregister(self):
        mock = Mock()
        TestEvent.register_handler(mock)
        TestEvent.deregister_handler(Mock)
        TestEvent.emit()
        mock.assert_not_called()