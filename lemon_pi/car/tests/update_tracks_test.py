import unittest

from lemon_pi.car.update_tracks import TrackUpdater


class TrackTestCase(unittest.TestCase):

    def test_validating_tmp_file(self):
        tu = TrackUpdater()
        self.assertTrue(tu.valid_yaml("resources/test/test-tracks.yaml"))
        self.assertFalse(tu.valid_yaml("resources/test/empty-tracks.yaml"))
        self.assertFalse(tu.valid_yaml("resources/test/corrupt-tracks.yaml"))


if __name__ == '__main__':
    unittest.main()
