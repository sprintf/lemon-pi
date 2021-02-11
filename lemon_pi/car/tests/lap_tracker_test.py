

import unittest
from unittest.mock import Mock
import time

from lemon_pi.car.event_defs import LeaveTrackEvent, RadioSyncEvent
from lemon_pi.car.lap_tracker import angular_difference, LapTracker
from lemon_pi.car.track import TrackLocation


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

    def test_time_crossing_line(self):
        bw = TrackLocation("bw", 35.489031,-119.544530, 35.488713,-119.544510, "E")
        lu = Mock()
        RadioSyncEvent.emit = Mock()
        lt = LapTracker(bw, lu)
        lt.on_track = True
        lt.lap_count = 0
        now = time.time()
        lt.update_position(35.4888, -119.5450, 90, now + 60, 50)
        lt.update_position(35.4888, -119.5446, 90, now + 61, 50)
        lt.update_position(35.4888, -119.5444, 90, now + 62, 50)
        lu.update_lap.assert_called_once()
        self.assertEqual(1, lu.update_lap.call_args[0][0])
        self.assertAlmostEqual(61.44, lu.update_lap.call_args[0][1], places=2)
        RadioSyncEvent.emit.assert_called_once()
        self.assertEqual(1, lt.lap_count)
        self.assertAlmostEqual(61.44, lt.last_lap_time, places=2)

    def test_pit_in_detection(self):
        bw = TrackLocation("bw", 35.489031,-119.544530, 35.488713,-119.544510, "E")
        bw.set_pit_in_coords((35.489031,-119.546), (35.488713,-119.546), "E")
        LeaveTrackEvent.emit = Mock()
        lt = LapTracker(bw, Mock())
        lt.on_track = True
        now = time.time()
        lt.update_position(35.4889, -119.5462, 90, now + 60, 50)
        lt.update_position(35.4889, -119.5458, 90, now + 61, 50)
        LeaveTrackEvent.emit.assert_called_once()
        self.assertEqual(now + 61, lt.last_pit_in_time)

if __name__ == '__main__':
    unittest.main()