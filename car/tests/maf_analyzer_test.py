import unittest

from car.maf_analyzer import MafAnalyzer

from python_settings import settings
import config.test_settings as my_local_settings

if not settings.configured:
    settings.configure(my_local_settings)


class MafTestCase(unittest.TestCase):

    def test_initial_fuel_remaining(self):
        ma = MafAnalyzer(None)
        self.assertEqual(-1, ma.get_fuel_percent_remaining())

    def test_no_fuel_remaining(self):
        ma = MafAnalyzer(None)
        ma.total_fuel_used_ml = 10.5 * 3785
        self.assertEqual(0, ma.get_fuel_percent_remaining())


if __name__ == '__main__':
    unittest.main()
