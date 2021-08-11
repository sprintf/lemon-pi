import os
import pickle

from lemon_pi.car.gate import Gates
from lemon_pi.car.track import TrackLocation


class LapSessionStore:
    # Used to store session data. The

    __instance = None

    def __init__(self, track: TrackLocation):
        self.track = track

    @classmethod
    def init(cls, track: TrackLocation):
        LapSessionStore.__instance = LapSessionStore(track)
        os.makedirs("/var/lib/lemon-pi/track-data")

    @classmethod
    def get_instance(cls) :
        return LapSessionStore.__instance

    def load_sessions(self) -> Gates:
        # todo : load all sessions for this track
        gates = []
        for session in os.listdir():
            gates.append(pickle.load(session))
        return gates

    def save_session(self, gates: Gates):
        # todo : create path from base + track + current session if there is one
        # if there's enough data, then write it back
        # todo : write a time into the file, so we know when it was run ... if it was
        # on same day (or day before) we take it straight away
        # todo : filename should be the track length
        # todo : put versioning into the name
        pickle.dump(gates, "TBD")
        pass