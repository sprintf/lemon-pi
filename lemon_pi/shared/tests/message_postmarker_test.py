import unittest

from lemon_pi.shared.message_postmarker import MessagePostmarker
from lemon_pi_pb2 import ToCarMessage, ToPitMessage


class PostmarkerTestCase(unittest.TestCase):

    def setUp(self):
        MessagePostmarker.instance = None

    def test_postmarking_first_time(self):
        m = ToCarMessage()
        m.ping.gps.speed_mph = 100
        stamper = MessagePostmarker.get_instance("sender")
        v = stamper.seq
        stamper.stamp(m)
        self.assertEqual(v + 1, m.ping.seq_num)
        self.assertEqual("sender", m.ping.sender)
        self.assertEqual(v + 1, stamper.seq)

    def test_postmarking_toPitMessage(self):
        m = ToPitMessage()
        m.ping.gps.speed_mph = 100
        stamper = MessagePostmarker.get_instance("sender")
        v = stamper.seq
        stamper.stamp(m)
        self.assertEqual(v + 1, m.ping.seq_num)
        self.assertEqual("sender", m.ping.sender)
        self.assertEqual(v + 1, stamper.seq)

    def test_postmarked_messages_untouched(self):
        m = ToPitMessage()
        m.ping.gps.speed_mph = 100
        stamper = MessagePostmarker.get_instance("sender")
        v = stamper.seq
        stamper.stamp(m)
        self.assertEqual(v + 1, m.ping.seq_num)
        stamper.stamp(m)
        stamper.stamp(m)
        self.assertEqual(v + 1, m.ping.seq_num)
        self.assertEqual("sender", m.ping.sender)
        self.assertEqual(v + 1, stamper.seq)

