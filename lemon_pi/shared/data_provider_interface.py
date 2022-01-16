from lemon_pi_pb2 import GpsPosition


class GpsProvider:

    # returns None if there's nothing up to date
    def get_gps_position(self) -> GpsPosition:
        pass
