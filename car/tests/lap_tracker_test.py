

import unittest
from car.lap_tracker import angular_difference


class TestAngularDifference(unittest.TestCase):

    def test_angular_difference(self):
        self.assertEqual(angular_difference(10, 20), 10)
        self.assertEqual(angular_difference(20, 10), 10)
        self.assertEqual(angular_difference(15, 15), 0)
        self.assertEqual(angular_difference(359, 1), 2)
        self.assertEqual(angular_difference(10, 200), 170)
        self.assertEqual(angular_difference(200, 10), 170)
        self.assertEqual(angular_difference(0, 180), 180)
        self.assertEqual(angular_difference(180, 0), 180)

if __name__ == '__main__':
    unittest.main()