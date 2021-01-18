import unittest

from car.obd_reader import ObdReader


class ObdReaderTest(unittest.TestCase):

    def test_zero_trim(self):
        r = ObdReader(None)
        r.short_term_fuel_trim = 0
        r.long_term_fuel_trim = 0
        self.assertAlmostEqual(r.calc_fuel_rate(14.39), 1.31, places=2)

    def test_idle_trim_canceled(self):
        r = ObdReader(None)
        r.short_term_fuel_trim = 0.78125
        r.long_term_fuel_trim = -0.78125
        self.assertAlmostEqual(r.calc_fuel_rate(3.42), 0.31, places=2)

    def test_idle_trim(self):
        r = ObdReader(None)
        r.short_term_fuel_trim = -1.5625
        r.long_term_fuel_trim = -0.78125
        self.assertAlmostEqual(r.calc_fuel_rate(3.4), 0.30, places=2)

    def test_2500_rpm(self):
        r = ObdReader(None)
        r.short_term_fuel_trim = 4.6875
        r.long_term_fuel_trim = -0.78125
        self.assertAlmostEqual(r.calc_fuel_rate(12.43), 1.18, places=2)

    def test_3500_rpm(self):
        r = ObdReader(None)
        r.short_term_fuel_trim = -2.34
        r.long_term_fuel_trim = 0.0
        self.assertAlmostEqual(r.calc_fuel_rate(15.0), 1.33, places=2)

if __name__ == '__main__':
    unittest.main()
