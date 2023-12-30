
class PositionUpdater:

    def update_position(self, lat: float, long: float, heading: float, time: float,
                        speed: int, linear_g: float, lateral_g: float) -> None:
        pass


class LapUpdater:

    def update_lap(self, lap_count: int, last_lap_time: float):
        pass
