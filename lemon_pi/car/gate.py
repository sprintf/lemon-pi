import time

from haversine import haversine, Unit

from lemon_pi.car import geometry
from lemon_pi.car.line_cross_detector import LineCrossDetector
from lemon_pi.car.target import Target
from statistics import mean
import bisect
import logging

logger = logging.getLogger(__name__)

# why 18? after running the predictive lap timer test on lots of different
# values between 12 and 100, 18 turned out to be a pretty good result
ELEMENTS = 18


class Gates:

    def __init__(self, start_finish: Target):
        self.start_finish = start_finish
        self.gates: [Gate] = []
        self.timestamp = time.time()

    def __iter__(self):
        return self.gates.__iter__()

    def __len__(self):
        return self.gates.__len__()

    def __getitem__(self, item):
        return self.gates.__getitem__(item)

    def append(self, thing):
        return self.gates.append(thing)

    def get_distance_feet(self) -> int:
        last_lat_long = self.start_finish.midpoint
        total_distance_feet = 0
        for gate in self.gates:
            total_distance_feet += haversine(last_lat_long, (gate.lat, gate.long), Unit.FEET)
            last_lat_long = gate.lat, gate.long
        total_distance_feet += haversine(last_lat_long, self.start_finish.midpoint, Unit.FEET)
        return int(total_distance_feet)

    def stamp_time(self):
        self.timestamp = time.time()

    def lap_count(self):
        return len(self.gates[0].times_from_start)


class Gate:
    # A Gate is a virtual gps gate across the track.  The track is divided up
    # into dozens of gates, and each gate holds a list of typical times
    # taken to arrive at the gate as well as typical times to complete the lap
    # from each gate. These arrays are constantly updating as more data is added.
    #
    # Gates are stored with a back pointer to the previous gate, and times are
    # also stored to indicate typical travel times between consecutive gates.
    #
    # At the end of each lap, the actual times from each gate to the end of the lap
    # are captured and stored.
    #
    # As each gate is passed, the time from the start of the lap is stored, and
    # the time from the previous gate.
    #
    # Prediction is based on looking at the ranking of how fast the car has
    # traversed the last few gates, and then using that ranking to select the
    # similarly ranked time to the end of the lap.

    def __init__(self, lat, long, heading, name, previous=None):
        # static fields : these are fixed
        self.lat = lat
        self.long = long
        self.heading = heading
        self.target = self._create_target(name)
        # back pointer to the previous gate
        self.previous: Gate = previous

        # dynamic fields .. these change as more lap data is added
        self.missed = False
        self.times_from_start: [float] = []
        self.times_from_prev: [float] = []
        self.times_to_finish: [float] = []
        self.last_time_from_start: float = 0
        # the most recent index into the sorted lap times
        self.last_mini_rank = -1

    def record_time_from_start(self, t):
        if t < 0:
            raise Exception()
        self.last_time_from_start = t
        bisect.insort(self.times_from_start, t)
        self._trim_data(self.times_from_start, ELEMENTS, t)
        if self.previous and not self.previous.missed:
            mini_split = t - self.previous.last_time_from_start
            if len(self.times_from_prev):
                mini_split_improvement = (self.times_from_prev[0] - mini_split) / self.times_from_prev[0] * 100
                if len(self.times_from_prev) > 3 and mini_split_improvement > 35:
                    logger.debug(f"{self.target.name} disregarding {mini_split_improvement:0.2f}%")
                    self.missed = True
                    return
            if mini_split > 0:
                bisect.insort(self.times_from_prev, mini_split)
                self._trim_data(self.times_from_prev, ELEMENTS, mini_split)

    def coords(self):
        return self.lat, self.long

    def predict_lap(self, elapsed_time):
        # given how long it has taken to get to this gate, predict how long it
        # will take to complete the lap from here.
        if elapsed_time < 0:
            raise Exception()
        ranking = bisect.bisect_left(self.times_from_start, elapsed_time)
        logger.debug(f"searching for {elapsed_time} returns {ranking}")
        best_est_rank = ranking
        if self.previous:
            # take a look at the 5 most recent gates, and where we ranked in getting from
            # them to here
            if not self.previous.missed:
                mini_split = elapsed_time - self.previous.last_time_from_start
                self.last_mini_rank = bisect.bisect_left(self.times_from_prev, mini_split)
            else:
                self.last_mini_rank = best_est_rank
            recent_ranks = self._gather_recent_mini_splits()
            if len(recent_ranks):
                best_est_rank = round((mean(recent_ranks) + best_est_rank) / 2)
        if best_est_rank >= len(self.times_to_finish):
            best_est_rank = -1
        return elapsed_time + self.times_to_finish[best_est_rank]

    def record_lap_time(self, lap_time):
        if self.missed:
            return
        if lap_time < 0:
            raise Exception()
        actual_completion_time = lap_time - self.last_time_from_start
        if actual_completion_time > 0:
            bisect.insort(self.times_to_finish, actual_completion_time)
            self._trim_data(self.times_to_finish, ELEMENTS, actual_completion_time)

    def _create_target(self, gate_name):
        heading_left = (self.heading + 270) % 360
        heading_right = (self.heading + 90) % 360
        # todo : the expansion factor should be based on the width of the track
        gate_lat_long1 = geometry.get_point_on_heading((self.lat, self.long), heading_left, 0.02)
        gate_lat_long2 = geometry.get_point_on_heading((self.lat, self.long), heading_right, 0.02)
        return Target(gate_name, gate_lat_long1, gate_lat_long2, target_heading=self.heading)

    @staticmethod
    def _trim_data(sorted_list, max_size, new_data):
        if len(sorted_list) > max_size:
            if sorted_list[-1] == new_data and new_data / sorted_list[-2] < 1.3:
                # if we just added this as the slowest, and it's not more than
                # 1.3 times off from a reasonable time
                # then remove a middle element
                sorted_list.pop(round(ELEMENTS / 2))
            else:
                sorted_list.pop(-1)

    def _gather_recent_mini_splits(self) -> [int]:
        results: [int] = []
        scanner = self
        while scanner.previous and len(results) < 5:
            if not scanner.missed:
                results.append(scanner.last_mini_rank)
            scanner = scanner.previous
        return results


class GateVerifier:

    def __init__(self, gates: Gates):
        self.gates = gates
        self.cross_detector = LineCrossDetector()
        self.index = 0
        self.matched = 0

    def is_match(self):
        return self.matched == len(self.gates)

    def get_distance_feet(self):
        return self.gates.get_distance_feet()

    def get_timestamp(self):
        return self.gates.timestamp

    def verify(self, lat, long, heading, time):
        if self.index >= len(self.gates):
            return
        crossed, crossed_time = self.cross_detector.crossed_line(lat,
                                                                 long,
                                                                 heading,
                                                                 time,
                                                                 self.gates[self.index].target)
        if crossed:
            self.index += 1
            self.matched += 1
        else:
            # did we miss a gate?
            if self.index < len(self.gates) - 1:
                gate_dist = haversine((lat, long), self.gates[self.index].target.midpoint, Unit.FEET)
                next_gate_dist = haversine((lat, long), self.gates[self.index + 1].target.midpoint,
                                           Unit.FEET)
                if gate_dist > next_gate_dist:
                    self.index += 1