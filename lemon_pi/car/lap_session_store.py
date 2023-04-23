import os
import pickle
import logging

from lemon_pi.car.gate import Gates
from lemon_pi.car.track import TrackLocation

logger = logging.getLogger(__name__)


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
        # load all sessions for this track, sort them from most recent to least
        result = []
        for file in os.listdir(self.basedir):
            if file.endswith("-v1.dat"):
                with open(os.path.join(self.basedir, file), "rb") as f:
                    try:
                        result.append(pickle.load(f))
                    except ModuleNotFoundError:
                        # ignore unloadable old content, this happens due to pickle failure
                        pass
        logger.info(f"loaded {len(result)} track configurations with previous data")
        result.sort(key=lambda a: a.timestamp, reverse=True)
        return result

    def save_session(self, gates: Gates):
        filename = f"{gates.get_distance_feet()}-v1.dat"
        file = os.path.join(self.basedir, filename)
        logger.info(f"saving session data in {file}")
        if gates.lap_count() > 3:
            with open(file, "wb") as f:
                pickle.dump(gates, f)
                f.flush()
            logger.info(f"data written, file created {file}")
