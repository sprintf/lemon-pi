

import unittest
from unittest.mock import MagicMock, patch
from shared.radio import Radio
from shared.generated.messages_pb2 import Ping

class RadioTestCase(unittest.TestCase):

    # def test_radio(self):
    #     radio = Radio("team", "password", ser=MagicMock())
    #     radio.receive_loop()

    def test_sending_message(self):
        radio = Radio("team", "password", ser=MagicMock())
        protocol = MagicMock()
        protocol.send_cmd = MagicMock()
        radio.send_message(protocol, Ping())


        # expect four calls : stop receiving, light on, tx, light off
        self.assertEqual(4, protocol.send_cmd.call_count)
        self.assertEqual("radio rxstop", protocol.send_cmd.call_args_list[0].args[0])
        self.assertEqual("sys set pindig GPIO11 1", protocol.send_cmd.call_args_list[1].args[0])
        self.assertTrue(protocol.send_cmd.call_args_list[2].args[0].startswith("radio tx "))
        self.assertEqual("sys set pindig GPIO11 0", protocol.send_cmd.call_args_list[3].args[0])

