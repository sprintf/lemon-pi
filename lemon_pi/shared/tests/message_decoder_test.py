import unittest

from lemon_pi.shared.message_encoder import MessageEncoder

from lemon_pi.shared.message_decoder import (
    MessageDecoder,
    NoiseException,
    LPiNoiseException
)
from lemon_pi.shared.message_postmarker import MessagePostmarker
from lemon_pi_pb2 import ToCarMessage, ToPitMessage


class DecoderTestCase(unittest.TestCase):

    def setUp(self):
        MessagePostmarker.instance = None

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

    def test_decoding_message_from_other_car(self):
        e = MessageEncoder("car-1", "pswd")
        msg = ToPitMessage()
        msg.pitting.seq_num = 1
        msg.pitting.timestamp = 2
        msg.pitting.sender = "car-1"
        binary_message = e.encode(msg)
        m = MessageDecoder("pswd")
        result = m.decode(binary_message, ToCarMessage())
        print(result)





if __name__ == '__main__':
    unittest.main()
