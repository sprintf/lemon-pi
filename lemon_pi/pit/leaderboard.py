

# a data structure representing a row in the leaderboard.
# the leaderboard is a double linked list, where each element
# contains a pointer to the `car_in_front` and another to the
# `car_behind`.
from enum import Enum

from lemon_pi.pit.event_defs import DumpLeaderboardEvent
from lemon_pi.shared.events import EventHandler


class PositionEnum(Enum):
    OVERALL = 1
    IN_CLASS = 2


class CarPosition:

    NOT_STARTED = 99999

    def __init__(self, car_number, name, class_id=None):
        self.car_number = car_number
        self.team_driver_name = name
        self.class_id = class_id
        self.position = CarPosition.NOT_STARTED
        self.class_position = CarPosition.NOT_STARTED
        self.laps_completed = 0
        # float, seconds and parts of seconds
        self.last_lap_time: float = 0.0
        self.last_lap_timestamp = None
        # float, seconds and parts of seconds
        self.fastest_lap_time = None
        self.fastest_lap = None
        self.car_in_front: CarPosition = None
        self.car_behind: CarPosition = None

    def get_car_in_front(self, position_mode: PositionEnum):
        if position_mode == PositionEnum.OVERALL:
            return self.car_in_front
        else:
            cursor: CarPosition = self.car_in_front
            while cursor and cursor.class_id != self.class_id:
                cursor = cursor.car_in_front
            return cursor

    def get_position(self):
        return self.position

    def get_position_in_class(self):
        return self.class_position

    def __repr__(self):
        return "#{} {}th laps:{} by {} last: {} best: {} on lap {}".\
            format(self.car_number,
                   self.position,
                   self.laps_completed,
                   self.gap(self.car_in_front),
                   self.last_lap_time,
                   self.fastest_lap_time,
                   self.fastest_lap)

    # produce a human readable format of the gap. This could be in the form:
    #   5 L    gap is 5 laps
    #   7 L(p) car is in pits
    #   4:05
    #   12s
    # It takes no more than 7 characters to display
    def gap(self, car_ahead):

        # take care of the situation where this car is the leader
        if car_ahead is None:
            return "-"

        seconds_diff = -1
        if car_ahead.last_lap_timestamp and self.last_lap_timestamp:
            seconds_diff = int((self.last_lap_timestamp - car_ahead.last_lap_timestamp) / 1000)

        if car_ahead.laps_completed and self.laps_completed:
            lap_diff = car_ahead.laps_completed - self.laps_completed
            if lap_diff > 0:
                # if it's been more than 5 minutes between one of these two cars
                # crossed the line, then one or both are pitted
                if seconds_diff < 300:
                    return "{} L".format(lap_diff)
                else:
                    return "{} L(p)".format(lap_diff)
        if seconds_diff > 0:
            if seconds_diff >= 60:
                minutes_diff = int(seconds_diff / 60)
                seconds_diff = seconds_diff % 60
                return "{}:{:02d}".format(minutes_diff, seconds_diff)
            else:
                return "{}s".format(seconds_diff)
        return "-"


# The RaceOrder is the main data structure that indexes and manages the
# CarPosition.
# It updates as cars pass the start/finish line
class RaceOrder(EventHandler):

    def __init__(self):
        self.first = None
        self.number_lookup = {}
        self.class_lookup = {}
        DumpLeaderboardEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == DumpLeaderboardEvent:
            print(self.__repr__())

    def lookup(self, car_number) -> CarPosition:
        return self.number_lookup.get(car_number)

    def get_car_in_position(self, position):
        cursor: CarPosition = self.first
        loop = 0
        while cursor and loop <= position:
            if cursor.position == position:
                return cursor
            cursor = cursor.car_behind
            loop += 1
        return None

    def add_car(self, car: CarPosition):
        existing = self.number_lookup.get(car.car_number)
        if not existing:
            self.number_lookup[car.car_number] = car
            self.first = self.__append__(self.first, car)
            existing = car
        return existing

    def add_class(self, class_id, name):
        self.class_lookup[class_id] = name

    def has_multiple_classes(self) -> bool:
        return len(self.class_lookup) > 1

    def size(self):
        return len(self.number_lookup)

    def update_position(self, car_number, position, lap_count):
        car = self.number_lookup.get(car_number)
        if not car:
            car = self.add_car(CarPosition(car_number, "unknown"))
        # the lap_count can be passed in as none
        if lap_count:
            car.laps_completed = lap_count
            car.position = position

        self.__adjust_position__(car)
        # renumber the field
        self.cleanup()
        # self.__check_data_structure__()

    def update_last_lap(self, car_number, last_lap_time: float):
        if not isinstance(last_lap_time, float):
            raise Exception("lap time is not a float")
        car = self.number_lookup.get(car_number)
        if not car:
            car = self.add_car(CarPosition(car_number, "unknown"))
        car.last_lap_time = last_lap_time

    def update_fastest_lap(self, car_number, fastest_lap_number, fastest_lap_time: float):
        if not isinstance(fastest_lap_time, float):
            raise Exception("lap time is not a float")
        car = self.number_lookup.get(car_number)
        if not car:
            car = self.add_car(CarPosition(car_number, "unknown"))
        car.fastest_lap = fastest_lap_number
        car.fastest_lap_time = fastest_lap_time

    def update_lap_timestamp(self, car_number, timestamp):
        car = self.number_lookup.get(car_number)
        if not car:
            car = self.add_car(CarPosition(car_number, "unknown"))
        car.last_lap_timestamp = timestamp

    def __append__(self, target: CarPosition, car: CarPosition):
        if target is None:
            return car
        target.car_behind = self.__append__(target.car_behind, car)
        target.car_behind.car_in_front = target
        return target

    # adjust the position of a car, whatever it's ultimate position is
    # there can be no cars ahead of it with a position greater or equal
    # and there can be no car behind with a position less than or equal
    def __adjust_position__(self, car: CarPosition):
        # there's nothing but us
        if not car.car_behind and not car.car_in_front:
            return

        # # if we're in the right spot
        # if car.car_behind and car.position == CarPosition.NOT_STARTED and \
        #     car.car_behind.position == CarPosition.NOT_STARTED:
        #     return
        #
        # # not sure this is legit short circuit
        # if car.car_behind and car.position < car.car_behind.position and \
        #    car.car_in_front and car.position > car.car_in_front.position:
        #     return

        # scan forwards and backwards to find insertion point
        insert_after = self.__find_insertion_point__(car)

        # if we're already at the right place then we're finished
        if insert_after == car:
            return

        former_in_front = car.car_in_front
        former_behind = car.car_behind

        if insert_after is None:
            # this happens when the car is moving to first
            self.first.car_in_front = car
            car.car_behind = self.first
            car.car_in_front = None
            self.first = car
        else:
            # store some markers
            insert_point_car_behind = insert_after.car_behind

            # wire us up into the new spot
            car.car_in_front = insert_after
            car.car_behind = insert_point_car_behind

            # wire the car ahead and behind to point to us
            if insert_point_car_behind:
                insert_point_car_behind.car_in_front = car

            insert_after.car_behind = car

        # where we removed ourselves from, we cross wire
        if former_in_front:
            former_in_front.car_behind = former_behind

        if former_behind:
            former_behind.car_in_front = former_in_front

        # finally, renumber all the cars into new positions
        self.cleanup()

    def __find_insertion_point__(self, car: CarPosition):
        scan = car.car_in_front
        iterations = 0
        while scan and (scan.laps_completed < car.laps_completed or scan.position == CarPosition.NOT_STARTED):
            scan = scan.car_in_front
            iterations += 1

        if iterations > 0:
            return scan

        # let's try going backwards instead of forwards
        if iterations == 0:
            prev = car
            scan = car.car_behind
            while scan and scan.laps_completed >= car.laps_completed and scan.position != CarPosition.NOT_STARTED:
                prev = scan
                scan = scan.car_behind

            return prev

        return car

    def __check_data_structure__(self):
        expected_size = len(self.number_lookup)
        # can scan from front to back
        scan = self.first
        last = None
        count = 0
        while scan and count < expected_size:
            if scan.car_behind is None:
                last = scan
            scan = scan.car_behind
            count += 1

        assert scan is None and count == expected_size

        # can scan from back to front
        count = 0
        scan = last
        while scan and count < expected_size:
            scan = scan.car_in_front
            count += 1

        assert scan is None and count == expected_size, \
            "scan = {}, count = {}, expected_size = {}".format(scan, count, expected_size)

        # position is correct for each one...any with no position
        # set must be all at the end of the list
        if self.first and self.first.position != CarPosition.NOT_STARTED:
            assert self.first.position == 1, self.__repr__()
            last_position = 0
            scan: CarPosition = self.first
            ns_encountered = False
            while scan:
                if scan.position == CarPosition.NOT_STARTED:
                    ns_encountered = True
                if ns_encountered:
                    assert scan.position == CarPosition.NOT_STARTED
                else:
                    assert scan.position == last_position + 1, \
                        "pos {} found car in pos {}\n{}".format(last_position + 1,
                                                                scan.position,
                                                                self.__repr__())
                    last_position = scan.position
                    if scan.car_in_front:
                        assert scan.car_in_front.laps_completed >= scan.laps_completed, \
                                scan.__repr__() + " isn't behind " + scan.car_in_front.__repr__()
                scan = scan.car_behind

        return True

    # go through the results and make them all sequential from 1 .. N
    def cleanup(self):
        pos = 1
        scan = self.first
        while scan and scan.position != CarPosition.NOT_STARTED:
            scan.position = pos
            pos += 1
            scan = scan.car_behind
        while scan:
            if scan.laps_completed == 0:
                scan.position = CarPosition.NOT_STARTED
            scan = scan.car_behind
        if self.has_multiple_classes():
            for race_class in self.class_lookup.keys():
                scan: CarPosition = self.first
                pos = 1
                while scan and scan.position != CarPosition.NOT_STARTED:
                    if scan.class_id == race_class:
                        scan.class_position = pos
                        pos += 1
                    scan = scan.car_behind

    def __repr__(self):
        result = ""
        scan = self.first
        while scan:
            result = result + "\n" + repr(scan)
            scan = scan.car_behind
        return result
