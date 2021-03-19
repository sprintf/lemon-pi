

import unittest
from unittest.mock import Mock, patch
import time

from lemon_pi.car.lap_tracker import angular_difference, LapTracker
from lemon_pi.car.target import Target
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

    @patch("lemon_pi.car.event_defs.RadioSyncEvent.emit")
    def test_time_crossing_line(self, radio_sync_event):
        bw = TrackLocation("bw")
        t = Target("start_finish", (35.489031,-119.544530), (35.488713,-119.544510), "E")
        bw.set_start_finish_target(t)
        lu = Mock()
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
        radio_sync_event.assert_called_once()
        self.assertEqual(1, lt.lap_count)
        self.assertAlmostEqual(61.44, lt.last_lap_time, places=2)

    @patch("lemon_pi.car.event_defs.LeaveTrackEvent.emit")
    def test_pit_in_detection(self, leave_track_event):
        bw = TrackLocation("bw")
        sf = Target("start-finiah", (35.489031,-119.544530), (35.488713,-119.544510), "E")
        bw.set_start_finish_target(sf)
        pi = Target("pit-in", (35.489031,-119.546), (35.488713,-119.546), "E")
        bw.set_pit_in_target(pi)
        lt = LapTracker(bw, Mock())
        lt.on_track = True
        now = time.time()
        lt.update_position(35.4889, -119.5462, 90, now + 60, 50)
        lt.update_position(35.4889, -119.5458, 90, now + 61, 50)
        leave_track_event.assert_called_once()

    @patch("lemon_pi.car.event_defs.RadioSyncEvent.emit")
    def test_radio_sync_detection(self, radio_sync_event):
        bw = TrackLocation("bw")
        sf = Target("start-finiah", (35.489031,-119.544530), (35.488713,-119.544510), "E")
        bw.set_start_finish_target(sf)
        pi = Target("radio", (35.489031,-119.546), (35.488713,-119.546), "E")
        bw.set_radio_sync_target(pi)
        lt = LapTracker(bw, Mock())
        lt.on_track = True
        now = time.time()
        lt.update_position(35.4889, -119.5462, 90, now + 60, 50)
        lt.update_position(35.4889, -119.5458, 90, now + 61, 50)
        radio_sync_event.assert_called_once()

if __name__ == '__main__':
    unittest.main()