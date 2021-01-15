import unittest

from shared.message_encoder import (
    MessageEncoder,
    MessageTooLongException
)
from shared.message_decoder import MessageDecoder
from shared.radio_message import *


class LongMessage(RadioMessageBase):

    def __init__(self):
        RadioMessageBase.__init__(self, "this-is-a-very-long-message-and-its-going-to-cause-problems")
        self.field1 = '01234567890'
        self.field2 = '09876543210'
        self.field3 = 'and theres more'
        self.field4 = 'youre not going to believe it'


class EncoderTestCase(unittest.TestCase):

    def test_encoding(self):
        e = MessageEncoder("car-180", "letmein")
        orig = PingMessage()
        payload = e.encode(orig)

        m = MessageDecoder("letmein")
        ping = m.decode(payload)
        self.assertEqual(orig.to_json(), ping.to_json())

    def test_message_too_long(self):
        e = MessageEncoder("car-180", "letmein")
        with self.assertRaises(MessageTooLongException):
            e.encode(LongMessage())


if __name__ == '__main__':
    unittest.main()
