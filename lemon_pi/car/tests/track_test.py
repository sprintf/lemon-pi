import re
import unittest
from lemon_pi.car.track import read_tracks, TrackLocation, swap_direction, do_read_tracks, START_FINISH, PIT_OUT, \
    PIT_ENTRY
from haversine import haversine, Unit


class TrackTestCase(unittest.TestCase):

    def test_change_heading(self):
        self.assertEquals(180, swap_direction(0))
        self.assertEquals(225, swap_direction(45))
        self.assertEquals(270, swap_direction(90))
        self.assertEquals(0, swap_direction(180))
        self.assertEquals(90, swap_direction(270))

    def test_read_test_file(self):
        tracks: [TrackLocation] = do_read_tracks("resources/test/test-tracks.yaml")
        test_track = next(filter(lambda track: track.name == "Arlington Test Track", tracks), None)
        self.assertTrue(test_track.is_reversed())
        self.assertAlmostEquals(330.1, test_track.targets[START_FINISH].target_heading, places=1)
        self.assertAlmostEquals(134.9, test_track.targets[PIT_OUT].target_heading, places=1)
        self.assertAlmostEquals(314.9, test_track.targets[PIT_ENTRY].target_heading, places=1)

    def test_read_tracks(self):
        tracks:[TrackLocation] = read_tracks()
        track_codes = set()
        for t in tracks:
            print(f"reading {t.name}")
            # this screws up the name gen in html
            self.assertTrue("," not in t.name)
            self.assertTrue(re.match("[a-zA-Z0-9-_]{3,6}", t.code))
            self.assertFalse(t.code in track_codes)
            track_codes.add(t.code)
            self.assertTrue(t.track_width_feet() > 25)
            self.assertTrue(t.track_width_feet() < 150)
            pit_to_sf1 = haversine(t.get_start_finish_target().lat_long1,
                                   t.get_pit_in_target().lat_long1,
                                   unit=Unit.MILES)
            pit_to_sf2 = haversine(t.get_start_finish_target().lat_long2,
                                   t.get_pit_in_target().lat_long2,
                                   unit=Unit.MILES)
            # distance from pit to start finish is less than a mile
            self.assertTrue(pit_to_sf1 < 1)
            self.assertTrue(pit_to_sf2 < 1)

        thunderhill = next(filter(lambda track: track.name == "Thunderhill", tracks), None)

if __name__ == '__main__':
    unittest.main()
