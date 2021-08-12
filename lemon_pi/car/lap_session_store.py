import os
import pickle

from lemon_pi.car.gate import Gates
from lemon_pi.car.track import TrackLocation


class LapSessionStore:

    __instance = None

    def __init__(self, track: TrackLocation, dir):
        self.track = track
        self.basedir = f"{dir}/{track.code}"
        if not os.path.isdir(self.basedir):
            os.makedirs(self.basedir)

    @classmethod
    def init(cls, track: TrackLocation, dir="/var/lib/lemon-pi/track-data/"):
        cls.__instance = LapSessionStore(track, dir)

    @classmethod
    def destroy(cls):
        cls.__instance = None

    @classmethod
    def get_instance(cls):
        return cls.__instance

    def load_sessions(self) -> [Gates]:
        # load all sessions for this track
        result = []
        for file in os.listdir(self.basedir):
            if file.endswith("-v1.dat"):
                with open(os.path.join(self.basedir, file), "rb") as f:
                    result.append(pickle.load(f))
        return result

    def save_session(self, gates: Gates):
        filename = f"{gates.get_distance_feet()}-v1.dat"
        if gates.lap_count() > 3:
            gates.stamp_time()
            with open(os.path.join(self.basedir, filename), "wb") as f:
                pickle.dump(gates, f)