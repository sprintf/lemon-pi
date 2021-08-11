import re
import unittest
from lemon_pi.car.track import read_tracks, TrackLocation
from haversine import haversine, Unit


class TrackTestCase(unittest.TestCase):

    def test_read_tracks(self):
        tracks:[TrackLocation] = read_tracks()
        for t in tracks:
            print(f"reading {t.name}")
            self.assertTrue(re.match("[a-zA-Z0-9-_]{3,6}", t.code))
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
        self.assertTrue(thunderhill.is_radio_sync_defined())
        self.assertEqual(2, len(thunderhill.get_radio_sync_targets()))

if __name__ == '__main__':
    unittest.main()
