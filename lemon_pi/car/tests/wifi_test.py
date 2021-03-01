import unittest

from lemon_pi.car.wifi import WifiManager

class WifiTest(unittest.TestCase):

    def test_command(self):
        response = WifiManager._command(["echo", "hello"])
        self.assertEqual(response, "hello")


if __name__ == '__main__':
    unittest.main()
