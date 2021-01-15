

import unittest
from unittest.mock import MagicMock, patch
from shared.radio import Radio
from shared.radio_message import PingMessage

class RadioTestCase(unittest.TestCase):

    def test_radio(self):
        radio = Radio("team", "password", ser=MagicMock())
        radio.receive_loop()

    @patch("shared.radio.Radio.write")
    def test_sending_message(self, magic:MagicMock):
        radio = Radio("team", "password", ser=MagicMock())
        protocol = MagicMock()
        radio.send_message(protocol, PingMessage())

        # ser should have has cancel_read called on it
        #self.ass
        # expect three calls : light on, tx, light off
        self.assertEqual(3, magic.call_count)
        self.assertEqual(b'sys set pindig GPIO11 1', magic.call_args_list[0].args[1])
        self.assertTrue(magic.call_args_list[1].args[1].startswith(b'radio tx '))
        self.assertEqual(b'sys set pindig GPIO11 0', magic.call_args_list[2].args[1])

