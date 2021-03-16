import unittest

from lemon_pi.shared.message_encoder import MessageEncoder

from lemon_pi.shared.message_decoder import (
    MessageDecoder,
    NoiseException,
    LPiNoiseException
)
from lemon_pi.shared.generated.messages_pb2 import ToCarMessage


class DecoderTestCase(unittest.TestCase):

    def test_decoding_noise(self):
        m = MessageDecoder("letmein")
        with self.assertRaises(NoiseException):
            m.decode(b'this is a message', ToCarMessage())

    def test_decoding_message_from_other_team(self):
        e = MessageEncoder("pit", "team-2")
        msg = ToCarMessage()
        msg.ping.timestamp = 1
        msg = e.encode(msg)
        m = MessageDecoder("team-1")
        with self.assertRaises(LPiNoiseException):
            m.decode(msg, ToCarMessage())




if __name__ == '__main__':
    unittest.main()
