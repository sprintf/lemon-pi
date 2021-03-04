import unittest

from lemon_pi.car.event_defs import RefuelEvent
from lemon_pi.car.maf_analyzer import MafAnalyzer

from python_settings import settings
import lemon_pi.config.test_settings as my_local_settings

if not settings.configured:
    settings.configure(my_local_settings)


class MafTestCase(unittest.TestCase):

    def test_initial_fuel_remaining(self):
        ma = MafAnalyzer(None)
        self.assertEqual(100, ma.get_fuel_percent_remaining())

    def test_no_fuel_remaining(self):
        ma = MafAnalyzer(None)
        ma.total_fuel_used_ml = 10.5 * 3785
        self.assertEqual(0, ma.get_fuel_percent_remaining())

    def test_refuel_100(self):
        ma = MafAnalyzer(None)
        ma.total_fuel_used_ml = 10000
        ma.handle_event(RefuelEvent, percent_full=100)
        self.assertEqual(100, ma.get_fuel_percent_remaining())

    def test_refuel_25(self):
        ma = MafAnalyzer(None)
        ma.total_fuel_used_ml = 10000
        ma.handle_event(RefuelEvent, percent_full=25)
        self.assertEqual(25, ma.get_fuel_percent_remaining())

if __name__ == '__main__':
    unittest.main()
