import unittest
from freezegun import freeze_time

from shared.time_provider import LocalTimeProvider


class MyTestCase(unittest.TestCase):

    @freeze_time("2021-01-08 12:21:34")
    def test_midday(self):
        tp = LocalTimeProvider()
        self.assertEqual(12, tp.get_hours())
        self.assertEqual(21, tp.get_minutes())
        self.assertEqual(34, tp.get_seconds())

    @freeze_time("2021-01-08 00:00:00")
    def test_midnight(self):
        tp = LocalTimeProvider()
        self.assertEqual(0, tp.get_hours())
        self.assertEqual(0, tp.get_minutes())
        self.assertEqual(0, tp.get_seconds())

    @freeze_time("2021-01-08 13:59:59")
    def test_midnight(self):
        tp = LocalTimeProvider()
        self.assertEqual(1, tp.get_hours())
        self.assertEqual(59, tp.get_minutes())
        self.assertEqual(59, tp.get_seconds())


if __name__ == '__main__':
    unittest.main()
