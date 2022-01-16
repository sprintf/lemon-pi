import unittest

from lemon_pi.shared.message_encoder import MessageEncoder
from lemon_pi.shared.message_decoder import MessageDecoder
from lemon_pi.shared.message_postmarker import MessagePostmarker

from lemon_pi_pb2 import ToCarMessage


class EncoderTestCase(unittest.TestCase):

    def setUp(self):
        MessagePostmarker.instance = None

    def test_encoding(self):
        e = MessageEncoder("car-180", "letmein")

        orig = ToCarMessage()
        orig.ping.timestamp = 1
        payload = e.encode(orig)

        m = MessageDecoder("letmein")
        ping = m.decode(payload, ToCarMessage())
        self.assertEqual("car-180", ping.sender)
        self.assertEqual(1, ping.seq_num)

    def test_refuel_roundtrip(self):
        e = MessageEncoder("car-180", "letmein")
        orig = ToCarMessage()
        orig.set_fuel.percent_full = 92
        payload = e.encode(orig)

        m = MessageDecoder("letmein")
        fuel = m.decode(payload, ToCarMessage())
        self.assertEqual("car-180", fuel.sender)
        self.assertEqual(1, fuel.seq_num)


if __name__ == '__main__':
    unittest.main()
