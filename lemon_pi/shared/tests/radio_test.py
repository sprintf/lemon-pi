

import unittest
from unittest.mock import MagicMock
from lemon_pi.shared.generated.messages_pb2 import Ping
from lemon_pi.shared.radio import Radio

from python_settings import settings
import lemon_pi.config.test_settings as my_local_settings

if not settings.configured:
    settings.configure(my_local_settings)

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

    def test_radio_freq(self):
        radio = Radio("team", "password", ser=MagicMock())
        map = {}
        for x in range(1, 80):
            freq = radio.__pick_radio_freq__(str(x))
            map[freq] = True
            self.assertTrue(int(freq / 100000) in Radio.FREQ)
        self.assertEqual(len(Radio.FREQ), len(map))

if __name__ == '__main__':
    unittest.main()