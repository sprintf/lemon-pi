
import unittest

from lemon_pi.shared.events import Event


class LemonPiTestCase(unittest.TestCase):

    def setUp(self) -> None:
        for e in Event.instance_iterator():
            e.last_event_time = 0
            e.handlers = []