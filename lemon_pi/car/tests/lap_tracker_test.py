

import unittest
from unittest.mock import patch
import time

from lemon_pi.car.event_defs import ResetFastLapEvent
from lemon_pi.car.lap_tracker import LapTracker
from lemon_pi.car.geometry import angular_difference
from lemon_pi.car.target import Target
from lemon_pi.car.track import TrackLocation, RADIO_SYNC

from python_settings import settings
import lemon_pi.config.test_settings as my_local_settings

if not settings.configured:
    settings.configure(my_local_settings)

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
        bw = TrackLocation("bw", "zoo")
        t = Target("start_finish", (35.489031, -119.544530), (35.488713, -119.544510), "E")
        bw.set_start_finish_target(t)
        lt = LapTracker(bw)
        lt.on_track = True
        lt.lap_count = 0
        now = time.time()
        lt.update_position(35.4888, -119.5450, 90, now + 60, 50)
        lt.update_position(35.4888, -119.5446, 90, now + 61, 50)
        lt.update_position(35.4888, -119.5444, 90, now + 62, 50)
        radio_sync_event.assert_called_once()
        self.assertEqual(1, lt.lap_count)
        self.assertAlmostEqual(61.44, lt.last_lap_time, places=2)

    @patch("lemon_pi.car.event_defs.LeaveTrackEvent.emit")
    def test_pit_in_detection(self, leave_track_event):
        bw = TrackLocation("bw", "foo")
        sf = Target("start-finish", (35.489031, -119.544530), (35.488713, -119.544510), "E")
        bw.set_start_finish_target(sf)
        pi = Target("pit-in", (35.489031, -119.546), (35.488713, -119.546), "E")
        bw.set_pit_in_target(pi)
        lt = LapTracker(bw)
        lt.on_track = True
        now = time.time()
        lt.update_position(35.4889, -119.5462, 90, now + 60, 50)
        lt.update_position(35.4889, -119.5458, 90, now + 61, 50)
        leave_track_event.assert_called_once()

    @patch("lemon_pi.car.event_defs.LeaveTrackEvent.emit")
    def test_pit_in_detection2(self, leave_track_event):
        bw = TrackLocation("ORP", "orp")
        sf = Target("start-finish", (45.363790,-120.744707),(45.363816,-120.744277), "S")
        bw.set_start_finish_target(sf)
        pi = Target("pit-in", (45.365624, -120.744398), (45.365573, -120.744325), "SW")
        bw.set_pit_in_target(pi)
        lt = LapTracker(bw)
        lt.on_track = True
        now = time.time()
        lt.update_position(45.365835,-120.744046667, 221, now + 60, 34)
        lt.update_position(45.365785,-120.74411, 221, now + 61, 32)
        lt.update_position(45.365736667,-120.744171667, 221, now + 62, 31)
        lt.update_position(45.365691667,-120.74423, 221, now + 63, 30)
        lt.update_position(45.365646667,-120.744285, 221, now + 64, 28)
        lt.update_position(45.365605,-120.744338333, 221, now + 65, 27)
        lt.update_position(45.365563333,-120.74439, 221, now + 66, 26)
        lt.update_position(45.365523333,-120.744438333, 219, now + 67, 25)
        lt.update_position(45.365483333,-120.744481667, 214, now + 68, 24)
        lt.update_position(45.36544,-120.744518333, 208, now + 69, 24)
        lt.update_position(45.365398333,-120.744546667, 203, now + 70, 23)
        leave_track_event.assert_called_once()

    @patch("lemon_pi.car.event_defs.RadioSyncEvent.emit")
    def test_radio_sync_detection(self, radio_sync_event):
        bw = TrackLocation("bw", "bar")
        sf = Target("start-finish", (35.489031, -119.544530), (35.488713, -119.544510), "E")
        bw.set_start_finish_target(sf)
        pi = Target("radio", (35.489031, -119.546), (35.488713, -119.546), "E")
        bw.add_target(RADIO_SYNC, pi)
        lt = LapTracker(bw)
        lt.on_track = True
        now = time.time()
        lt.update_position(35.4889, -119.5462, 90, now + 60, 50)
        lt.update_position(35.4889, -119.5458, 90, now + 61, 50)
        radio_sync_event.assert_called_once()

    def test_resetting_fastest_lap_time(self):
        bw = TrackLocation("bw", "foo")
        sf = Target("start-finish", (35.489031, -119.544530), (35.488713, -119.544510), "E")
        bw.set_start_finish_target(sf)
        lt = LapTracker(bw)
        lt.on_track = True
        lt.best_lap_time = 55.0
        ResetFastLapEvent.emit()
        self.assertEqual(None, lt.best_lap_time)


if __name__ == '__main__':
    unittest.main()
