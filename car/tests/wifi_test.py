import unittest

from car.wifi import WifiManager

class WifiTest(unittest.TestCase):

    def test_command(self):
        response = WifiManager().command(["echo", "hello"])
        self.assertEqual(response, "hello")


if __name__ == '__main__':
    unittest.main()
