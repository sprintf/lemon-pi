import unittest

from shared.message_encoder import MessageEncoder

from shared.message_decoder import (
    MessageDecoder,
    NoiseException,
    LPiNoiseException
)

from shared.radio_message import *


class DecoderTestCase(unittest.TestCase):

    def test_decoding_noise(self):
        m = MessageDecoder("letmein")
        with self.assertRaises(NoiseException):
            m.decode('this is a message')

    def test_decoding_message_from_other_team(self):
        e = MessageEncoder("pit", "team-2")
        msg = e.encode(PingMessage())
        m = MessageDecoder("team-1")
        with self.assertRaises(LPiNoiseException):
            m.decode(msg)




if __name__ == '__main__':
    unittest.main()
