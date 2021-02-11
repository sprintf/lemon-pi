import unittest
from lemon_pi.car.track import read_tracks, TrackLocation
from haversine import haversine, Unit

class MyTestCase(unittest.TestCase):
    def test_read_tracks(self):
        tracks:[TrackLocation] = read_tracks()
        for t in tracks:
            self.assertTrue(t.track_width_feet() > 25)
            self.assertTrue(t.track_width_feet() < 150)
            pit_to_sf1 = haversine(t.start_finish.lat_long1, t.pit_in.lat_long1, unit=Unit.MILES)
            pit_to_sf2 = haversine(t.start_finish.lat_long2, t.pit_in.lat_long2, unit=Unit.MILES)
            # distance from pit to start finish is less than a mile
            self.assertTrue(pit_to_sf1 < 1)
            self.assertTrue(pit_to_sf2 < 1)

if __name__ == '__main__':
    unittest.main()
