
import unittest
from unittest.mock import Mock, patch

from lemon_pi.car.gate import Gate, ELEMENTS, Gates, GateVerifier
from lemon_pi.car.target import Target
from lemon_pi.shared.data_provider_interface import GpsPos


class GateTest(unittest.TestCase):

    def test_prediction_fails_with_no_data(self):
        g = Gate(55, 100, 180, "gate-0")
        with self.assertRaises(IndexError):
            g.predict_lap(10)

    def test_prediction_with_one_time(self):
        g = Gate(55, 100, 180, "gate-0")
        g.record_time_from_start(15.0)
        g.record_lap_time(30.0)
        self.assertEqual(30.0, g.predict_lap(15.0))

    def test_throwing_out_extra_data(self):
        g = Gate(55, 100, 180, "gate-0")
        for x in range(20, 50):
            g.record_time_from_start(x)
            g.record_lap_time(x + 10)
        self.assertEqual(ELEMENTS, len(g.times_from_start))
        self.assertEqual(ELEMENTS, len(g.times_to_finish))
        # we should have the fastest and slowest times in there
        self.assertTrue(20 in g.times_from_start)
        self.assertTrue(49 in g.times_from_start)

    def test_really_slow_times_discarded(self):
        g = Gate(55, 100, 180, "gate-0")
        for x in range(20, 50):
            g.record_time_from_start(x)
            g.record_lap_time(x + 10)
        g.record_time_from_start(65)
        g.record_lap_time(75)
        self.assertFalse(65 in g.times_from_start)

    def test_slower_times_discarded(self):
        g = Gate(55, 100, 180, "gate-0")
        for x in range(20, 50):
            g.record_time_from_start(x)
            g.record_lap_time(x + 10)
        g.record_time_from_start(20)
        g.record_lap_time(31)
        self.assertFalse(49 in g.times_from_start)

    def test_multiple_gates(self):
        g1 = Gate(55, 100, 180, "gate-0")
        g2 = Gate(55, 100, 180, "gate-1", previous=g1)
        g3 = Gate(55, 100, 180, "gate-2", previous=g2)
        for x in range(20, 30):
            g1.record_time_from_start(x)
            g2.record_time_from_start(x + 5)
            g3.record_time_from_start(x + 10)
            g1.record_lap_time(x + 15)
            g2.record_lap_time(x + 15)
            g3.record_lap_time(x + 15)
        self.assertEqual(36, g1.predict_lap(21))
        self.assertEqual(36, g2.predict_lap(26))
        self.assertEqual(36, g3.predict_lap(31))


class GatesTest(unittest.TestCase):

    def test_gates(self):
        g = Gates(Target("foo", (0, 0), (1, 1), "N"))
        self.assertEqual(0, len(g))
        g.append(Gate(1, 0, 270, "gate-0"))
        self.assertEqual(1, len(g))
        self.assertEqual("gate-0", g[0].target.name)
        for i in g:
            self.assertEqual("gate-0", i.target.name)
        self.assertEqual(515900, g.get_distance_feet())
        self.assertEqual(0, g.lap_count())
        g[0].record_time_from_start(1.2)
        g[0].record_lap_time(56.3)
        self.assertEqual(1, g.lap_count())


class GateVerifierTest(unittest.TestCase):


    @patch("lemon_pi.car.gate.crossed_line")
    def test_good(self, crossed_line_mock):
        crossed_line_mock.return_value = (True, 1.0, False)
        gates = Gates(Target("foo", (0, 0), (1, 1), "N"))
        gate_array = []
        prev = None
        for i in range(0, 9):
            gate_array.append(Gate(1, 0, 270, f"gate-{i}", prev))
            prev = gate_array[i]
            gates.append(prev)
        gv = GateVerifier(gates)
        for i in range(0, 9):
            gv.verify(GpsPos(5, 5, 180, 0, 15), GpsPos(5, 5, 180, 0, 15))
        self.assertTrue(gv.is_match())

    @patch("lemon_pi.car.gate.crossed_line")
    def test_not_all_gates_crossed(self, crossed_line_mock):
        crossed_line_mock.return_value = (True, 1.0, False)
        gates = Gates(Target("foo", (0, 0), (1, 1), "N"))
        gate_array = []
        prev = None
        for i in range(0, 9):
            gate_array.append(Gate(1, 0, 270, f"gate-{i}", prev))
            prev = gate_array[i]
            gates.append(prev)
        gv = GateVerifier(gates)
        for i in range(0, 8):
            gv.verify(GpsPos(5, 5, 180, 0, 15), GpsPos(5, 5, 180, 0, 15))
        self.assertFalse(gv.is_match())
