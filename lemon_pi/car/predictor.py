import logging
from enum import Enum

from lemon_pi.car.gate import Gate
from lemon_pi.car.line_cross_detector import LineCrossDetector
from lemon_pi.car.target import Target
from haversine import haversine, Unit

logger = logging.getLogger(__name__)

from python_settings import settings


# todo : move this to settings
BREADCRUMB_DISTANCE_FEET = 200

# todo : write the gates into local storage
# see if there are gates defined when we decide on the track
# that saves on the breadcrumbing lap
# then also save separately the set of times : say every hour


class PredictorState(Enum):
    # we are awaiting crossing the start finish line
    INIT = 1,
    # we are on first full lap, and laying down breadcrumbs
    BREADCRUMB = 2,
    # we are working
    WORKING = 3


class LapTimePredictor:

    def __init__(self, start_finish: Target):
        self.start_finish = start_finish
        self.gates: [Gate] = []
        self.start_finish_detector = LineCrossDetector()
        self.gate_detector = LineCrossDetector(degrees=40)

        self.state = PredictorState.INIT

        self.last_heading = 0
        self.last_lat = 0
        self.last_long = 0
        self.last_time = 0

        self.lap_start_time = 0
        self.just_crossed_line = False
        self.current_predicted_time = None

        self.gate_index = -1

    def update_position(self, lat, long, heading, time):
        # throw out identical data, which some devices provide
        if lat == self.last_lat and long == self.last_long:
            return False, 0

        try:
            crossed_line, crossed_time = \
                self.start_finish_detector.crossed_line(lat, long, heading, time, self.start_finish)
            if crossed_line:
                self.gate_index = 0
                last_lap_time = crossed_time - self.lap_start_time
                self.lap_start_time = crossed_time
                if self.state == PredictorState.INIT:
                    self.state = PredictorState.BREADCRUMB
                elif self.state == PredictorState.BREADCRUMB:
                    self._update_gate_time_to_finish(last_lap_time)
                    self.state = PredictorState.WORKING
                elif self.state == PredictorState.WORKING:
                    self._update_gate_time_to_finish(last_lap_time)
                return crossed_line, crossed_time

            # we're on an out lap
            if self.state == PredictorState.INIT:
                return False, 0

            # we're on our first full lap laying breadcrumbs to figure out
            # where gates should be placed
            if self.state == PredictorState.BREADCRUMB:
                self._lay_breadcrumb(lat, long, heading)

            if self.state == PredictorState.WORKING:
                self._process_and_predict(lat, long, heading, time)

            return False, 0

        finally:
            self.last_heading = heading
            self.last_lat = lat
            self.last_long = long
            self.last_time = time

    # return the current predicted lap, or None if it cannot be predicted
    # The car needs to be 1/6th of the way around the track before the
    # predicted time appears. If the car has pitted and is on an out lap
    # then the predictor doesn't show
    def predict_lap(self):
        if self.state == PredictorState.WORKING:
            gate_count = len(self.gates)
            if gate_count / 6 <= self.gate_index < gate_count:
                return self.current_predicted_time
        return None

    def _lay_breadcrumb(self, lat, long, heading):
        if abs(heading - self.last_heading) > 20:
            return

        if len(self.gates) == 0:
            dist_from_sf = int(haversine(self.start_finish.midpoint, (lat, long), unit=Unit.FEET))
            if dist_from_sf >= settings.VGATE_SEPARATION_FEET:
                self.gates.append(Gate(lat, long, heading, "gate-0"))
                logger.info(f"added first gate, dist to sf = {dist_from_sf}")
        else:
            last_gate = self.gates[len(self.gates) - 1]
            dist_from_sf = int(haversine(self.start_finish.midpoint, (lat, long), unit=Unit.FEET))
            dist_from_last_gate = int(haversine(last_gate.coords(), (lat, long), unit=Unit.FEET))
            if dist_from_last_gate >= BREADCRUMB_DISTANCE_FEET:
                self.gates.append(Gate(lat, long, heading, f"gate-{len(self.gates)}", previous=last_gate))
                logger.info(f"added gate {len(self.gates)} dist to sf = {dist_from_sf}")

    def _process_and_predict(self, lat, long, heading, time):
        if self.gate_index < len(self.gates):
            crossed_gate, cross_gate_time = \
                self.gate_detector.crossed_line(lat, long, heading,
                                                time, self.gates[self.gate_index].target)
            if crossed_gate:
                self.gates[self.gate_index].missed = False
                elapsed_time = cross_gate_time - self.lap_start_time
                self.gates[self.gate_index].record_time_from_start(elapsed_time)
                # it's possible this throws an exception in the case this gate doesn't know
                # how long it takes to get to the end of the lap (perhaps it was missed on
                # all previous laps)
                try:
                    self.current_predicted_time = self.gates[self.gate_index].predict_lap(elapsed_time)
                    logger.info(
                        f"predicted lap time = {self.current_predicted_time:.02f}")
                except IndexError:
                    pass
                self.gate_index += 1
                self.gate_detector.reset()
            else:
                # see if we're nearer the next gate, if we are then we missed a gate
                if self.gate_index < len(self.gates) - 1:
                    gate_dist = haversine((lat, long), self.gates[self.gate_index].target.midpoint, Unit.FEET)
                    next_gate_dist = haversine((lat, long), self.gates[self.gate_index + 1].target.midpoint,
                                               Unit.FEET)
                    if gate_dist > next_gate_dist:
                        logger.info(f"missed gate {self.gate_index}!!!")
                        self.gates[self.gate_index].missed = True
                        self.gate_index += 1

    def _update_gate_time_to_finish(self, last_lap_time):
        mins = int(last_lap_time / 60)
        secs = int(last_lap_time % 60)
        logger.debug(f"lap completed in {mins:02d}:{secs:02d} ... updating gates")
        if last_lap_time > 210:
            return
        for g in self.gates:
            g.record_lap_time(last_lap_time)
