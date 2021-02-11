import unittest

from lemon_pi.shared.message_encoder import MessageEncoder
from lemon_pi.shared.message_decoder import MessageDecoder

from lemon_pi.shared.generated.messages_pb2 import Ping


class EncoderTestCase(unittest.TestCase):

    def test_encoding(self):
        e = MessageEncoder("car-180", "letmein")
        orig = Ping()
        payload = e.encode(orig)

        m = MessageDecoder("letmein")
        ping = m.decode(payload)
        self.assertEqual("car-180", ping.sender)
        self.assertEqual(1, ping.seq_num)


if __name__ == '__main__':
    unittest.main()
