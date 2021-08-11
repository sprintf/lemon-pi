import os
import pickle

from lemon_pi.car.gate import Gates
from lemon_pi.car.track import TrackLocation


class LapSessionStore:

    __instance = None

    def __init__(self, track: TrackLocation):
        self.track = track
        self.basedir = f"/var/lib/lemon-pi/track-data/{track.code}"
        os.makedirs(self.basedir)

    @classmethod
    def init(cls, track: TrackLocation):
        LapSessionStore.__instance = LapSessionStore(track)

    @classmethod
    def get_instance(cls) :
        return LapSessionStore.__instance

    def load_sessions(self) -> [Gates]:
        # load all sessions for this track
        result = []
        for file in os.listdir(self.basedir):
            if file.endswith("-v1.dat"):
                with open(file) as f:
                    result.append(pickle.load(f))
        return result

    def save_session(self, gates: Gates):
        filename = f"{gates.get_distance_feet()}-v1.dat"
        # todo : this needs implementing
        gates.stamp_time()
        # todo : don't write of theres no data
        with open(filename, "w") as f:
            pickle.dump(gates, f)