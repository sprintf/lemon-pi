import unittest

from shared.message_encoder import (
    MessageEncoder,
    MessageTooLongException
)
from shared.message_decoder import MessageDecoder
from shared.radio_message import *

from google.protobuf.message import Message
from shared.generated import ping_pb2


class EncoderTestCase(unittest.TestCase):

    def test_encoding(self):
        e = MessageEncoder("car-180", "letmein")
        orig = ping_pb2.Ping()
        payload = e.encode(orig)

        m = MessageDecoder("letmein")
        ping = m.decode(payload)
        self.assertEqual("car-180", ping.sender)
        self.assertEqual(1, ping.seq_num)


if __name__ == '__main__':
    unittest.main()
