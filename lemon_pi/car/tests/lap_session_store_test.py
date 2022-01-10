import os
import unittest

from lemon_pi.car.gate import Gates, Gate
from lemon_pi.car.lap_session_store import LapSessionStore
from lemon_pi.car.target import Target
from lemon_pi.car.track import TrackLocation


class LapSessionStoreTest(unittest.TestCase):

    @classmethod
    def tearDownClass(cls) -> None:
        for file in os.listdir("/tmp/test-lss/code"):
            os.remove(os.path.join("/tmp/test-lss/code", file))
        os.rmdir("/tmp/test-lss/code")
        os.rmdir("/tmp/test-lss")
        LapSessionStore.destroy()

    def test_initialization(self):
        track = TrackLocation('name', 'code')
        LapSessionStore.init(track, dir='/tmp/test-lss')
        self.assertTrue(os.path.isdir('/tmp/test-lss/code'))
        self.assertIsNotNone(LapSessionStore.get_instance())
        # test initialization with files there
        LapSessionStore.init(track, dir='/tmp/test-lss')

    def test_write_gate_date(self):
        track = TrackLocation('name', 'code')
        LapSessionStore.init(track, dir='/tmp/test-lss')
        gates = Gates(Target("goofy", (300, -500), (310, -800), "NW"))
        vgate = Gate(302, -450, 10, "gate-1")
        vgate.record_time_from_start(1.4)
        vgate.record_time_from_start(1.5)
        vgate.record_time_from_start(1.1)
        vgate.record_time_from_start(0.9)
        gates.append(vgate)
        LapSessionStore.get_instance().save_session(gates)
        saved_gates = LapSessionStore.get_instance().load_sessions()
        self.assertEqual(1, len(saved_gates))
        self.assertEqual(4, saved_gates[0].lap_count())
