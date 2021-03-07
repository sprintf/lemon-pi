import unittest
from unittest.mock import Mock

from lemon_pi.car.gps_reader import GpsReader
from lemon_pi.car.track import read_tracks
from haversine import haversine


class MainTestCase(unittest.TestCase):

    def test_selecting_home_track(self):
        self._test_position((37.928473, -122.297121), "Arlington Test Track")

    def test_selecting_nola_track(self):
        self._test_position((29.950345, -90.275897), "Nola Motorsports Park")

    def _test_position(self, target_position, expected_track):
        tracks = read_tracks()
        gps = GpsReader()
        gps.get_lat_long = Mock()
        gps.get_lat_long.return_value = target_position

        closest_track = min(tracks, key=lambda x: haversine(gps.get_lat_long(), x.get_start_finish_target().midpoint))
        self.assertEqual(expected_track, closest_track.name)



if __name__ == '__main__':
    unittest.main()
