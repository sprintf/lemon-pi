import re
import unittest
from lemon_pi.car.track import read_tracks, TrackLocation, swap_direction, do_read_tracks, START_FINISH, PIT_OUT, \
    PIT_ENTRY, Sector
from haversine import haversine, Unit


class TrackTestCase(unittest.TestCase):

    def test_change_heading(self):
        self.assertEqual(180, swap_direction(0))
        self.assertEqual(225, swap_direction(45))
        self.assertEqual(270, swap_direction(90))
        self.assertEqual(0, swap_direction(180))
        self.assertEqual(90, swap_direction(270))

    def test_read_test_file(self):
        tracks: [TrackLocation] = do_read_tracks("resources/test/test-tracks.yaml")
        test_track = next(filter(lambda track: track.name == "Arlington Test Track", tracks), None)
        self.assertTrue(test_track.is_reversed())
        self.assertAlmostEqual(330.1, test_track.targets[START_FINISH].target_heading, places=1)
        self.assertAlmostEqual(134.9, test_track.targets[PIT_OUT].target_heading, places=1)
        self.assertAlmostEqual(314.9, test_track.targets[PIT_ENTRY].target_heading, places=1)

    def test_reversing_track(self):
        tracks:[TrackLocation] = read_tracks()
        sonoma = next(filter(lambda track: track.name == "Sonoma Raceway", tracks), None)
        self.assertFalse(sonoma.is_reversed())
        sonoma.reverse()
        self.assertTrue(sonoma.is_reversed())
        sonoma.reverse()
        self.assertFalse(sonoma.is_reversed())

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

    def test_track_without_sectors(self):
        tracks = do_read_tracks("resources/test/test-tracks.yaml")
        arlington = next(filter(lambda t: t.name == "Arlington Test Track", tracks), None)
        self.assertFalse(arlington.has_sectors())
        self.assertEqual(0, len(arlington.sectors))

    def test_track_with_sectors(self):
        tracks = do_read_tracks("resources/test/test-tracks.yaml")
        track = next(filter(lambda t: t.name == "Sector Test Track", tracks), None)
        self.assertIsNotNone(track)
        self.assertTrue(track.has_sectors())
        self.assertEqual(3, len(track.sectors))

        # S1 - has gate coords
        self.assertEqual("S1", track.sectors[0].name)
        self.assertEqual(1, track.sectors[0].number)
        self.assertIsNotNone(track.sectors[0].target_meta_data)

        # S2 - has gate coords and direction
        self.assertEqual("S2", track.sectors[1].name)
        self.assertEqual(2, track.sectors[1].number)
        self.assertIsNotNone(track.sectors[1].target_meta_data)

        # S3 - last sector, no gate coords
        self.assertEqual("S3", track.sectors[2].name)
        self.assertEqual(3, track.sectors[2].number)
        self.assertIsNone(track.sectors[2].target_meta_data)

    def test_sector_targets(self):
        tracks = do_read_tracks("resources/test/test-tracks.yaml")
        track = next(filter(lambda t: t.name == "Sector Test Track", tracks), None)

        sector_targets = track.get_sector_targets()
        self.assertEqual(2, len(sector_targets))

        # S1 target
        sector, target = sector_targets[0]
        self.assertEqual("S1", sector.name)
        self.assertEqual("S1", target.name)
        self.assertAlmostEqual(37.927000, target.lat_long1[0], places=5)

        # S2 target with direction
        sector, target = sector_targets[1]
        self.assertEqual("S2", sector.name)
        self.assertNotEqual(0, target.target_heading)  # direction was parsed

if __name__ == '__main__':
    unittest.main()
