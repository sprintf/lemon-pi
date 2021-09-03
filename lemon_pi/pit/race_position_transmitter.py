from lemon_pi.pit.event_defs import (
    RadioReceiveEvent,
    LapCompletedEvent,
    LeavingPitEvent,
)
from lemon_pi.pit.leaderboard import (
    RaceOrder,
    PositionEnum,
)
from lemon_pi.shared.events import EventHandler


class RacePositionTransmitter(EventHandler):
    """ when the system first starts up, and cars connect/ping for the first time,
        we want to send them where they are in the race.
        We also send them their position as the car enters the track"""

    def __init__(self, leaderboard: RaceOrder):
        self.leaderboard = leaderboard
        self.target_cars = {}
        RadioReceiveEvent.register_handler(self)
        LeavingPitEvent.register_handler(self)

    def handle_event(self, event, car="", **kwargs):
        if event == LeavingPitEvent:
            # always send the race position when the car leaves the track
            self.send_race_position(car)
            return

        if event == RadioReceiveEvent:
            # send a race position the first time we hear from a car
            if car not in self.target_cars:
                # look up it's position in the race and send it to it
                if self.send_race_position(car):
                    self.target_cars[car] = True

    def send_race_position(self, car):
        pos = self.leaderboard.lookup(car)
        if pos:
            ahead = pos.get_car_in_front(PositionEnum.OVERALL)
            if ahead:
                LapCompletedEvent.emit(car=car,
                                       laps=pos.laps_completed,
                                       position=pos.position,
                                       class_position=pos.class_position,
                                       ahead=ahead.car_number,
                                       gap=pos.gap(ahead),
                                       last_lap_time=pos.last_lap_time)
            else:
                LapCompletedEvent.emit(car=car,
                                       laps=pos.laps_completed,
                                       position=pos.position,
                                       class_position=pos.class_position,
                                       ahead=None,
                                       gap='-',
                                       last_lap_time=pos.last_lap_time)
            return True
        return False
