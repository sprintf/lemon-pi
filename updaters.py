
class PositionUpdater:

    def update_position(self, lat:float, long:float, heading:float, time:float, speed:int) -> None:
        pass


class LapUpdater:

    def update_lap(self, lap_count: int, last_lap_time: float):
        pass

class MafUpdater:

    def update_maf(self, value:float, time:float):
        pass
