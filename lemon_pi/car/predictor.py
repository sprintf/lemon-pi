import logging
from typing import Optional

from python_settings import settings
from enum import Enum

from lemon_pi.car.event_defs import DriverMessageEvent, LeaveTrackEvent, ReverseTrackEvent
from lemon_pi.car.gate import Gate, Gates, GateVerifier
from lemon_pi.car.gps_geometry import crossed_line
from lemon_pi.car.lap_session_store import LapSessionStore
from lemon_pi.car.target import Target
from haversine import haversine, Unit

from lemon_pi.shared.data_provider_interface import GpsPos
from lemon_pi.shared.events import EventHandler

logger = logging.getLogger(__name__)

ONE_DAY_IN_SECONDS = 24 * 3600
TWO_DAYS_IN_SECONDS = ONE_DAY_IN_SECONDS * 2


class PredictorState(Enum):
    # we are awaiting crossing the start finish line
    INIT = 1,
    # we are on first full lap, and laying down breadcrumbs
    BREADCRUMB = 2,
    # we are working
    WORKING = 3


class LapTimePredictor(EventHandler):

    last_gps: Optional[GpsPos]

    def __init__(self, start_finish: Target):
        self.start_finish = start_finish
        self.gates: Gates = Gates(start_finish)

        self.state = PredictorState.INIT

        self.last_gps = None

        self.lap_start_time = 0
        self.current_predicted_time = None

        self.gate_index = -1

        LeaveTrackEvent.register_handler(self)
        ReverseTrackEvent.register_handler(self)

        # load a set of gate verifiers for our previous sessions at this track
        self.gate_verifiers = []
        if LapSessionStore.get_instance():
            self.gate_verifiers = [GateVerifier(f) for f in LapSessionStore.get_instance().load_sessions()]

    def handle_event(self, event, **kwargs):
        if event == LeaveTrackEvent:
            LapSessionStore.get_instance().save_session(self.gates)
            return
        if event == ReverseTrackEvent:
            self.state = PredictorState.INIT
            self.gates: Gates = Gates(self.start_finish)
            self.gate_index = -1
            return

    def update_position(self, lat, long, heading, time):
        # throw out identical data, which some devices provide
        if self.last_gps is not None and lat == self.last_gps.lat and long == self.last_gps.long:
            return False, 0, False

        this_gps = GpsPos(lat, long, heading, 0, time)

        try:
            crossed, crossed_time, backwards = \
                crossed_line(self.last_gps, this_gps, self.start_finish)
            if crossed:
                self.gate_index = 0
                last_lap_time = crossed_time - self.lap_start_time
                self.lap_start_time = crossed_time
                if self.state == PredictorState.INIT:
                    self.state = PredictorState.BREADCRUMB
                    DriverMessageEvent.emit(text="learning track...", duration_secs=60)
                elif self.state == PredictorState.BREADCRUMB:
                    self._update_gate_time_to_finish(last_lap_time)
                    self._determine_gates(self.gates.get_distance_feet())
                    self.state = PredictorState.WORKING
                elif self.state == PredictorState.WORKING:
                    # if we load previous data and jump straight into working then the last_lap_time
                    # is from the epoch, so we ignore that
                    if last_lap_time < ONE_DAY_IN_SECONDS:
                        self._update_gate_time_to_finish(last_lap_time)
                return crossed_line, crossed_time, backwards

            # we're on an out lap
            if self.state == PredictorState.INIT:
                return False, 0, False

            # we're on our first full lap laying breadcrumbs to figure out
            # where gates should be placed
            if self.state == PredictorState.BREADCRUMB:
                self._lay_breadcrumb(lat, long, heading)
                # also, on this lap, try to match this lap against other sessions at
                # this track, so we can load previous data
                for verifier in self.gate_verifiers:
                    verifier.verify(self.last_gps, this_gps)

            if self.state == PredictorState.WORKING:
                self._process_and_predict(this_gps)

            return False, 0, False

        finally:
            self.last_gps = GpsPos(lat, long, heading, 0, time)

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
        if abs(heading - self.last_gps.heading) > 20:
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
            if dist_from_last_gate >= settings.VGATE_SEPARATION_FEET:
                self.gates.append(Gate(lat, long, heading, f"gate-{len(self.gates)}", previous=last_gate))
                logger.info(f"added gate {len(self.gates)} dist to sf = {dist_from_sf}")

    def _process_and_predict(self, this_gps: GpsPos):
        if self.gate_index < len(self.gates):
            crossed_gate, cross_gate_time, backwards = \
                crossed_line(self.last_gps, this_gps, self.gates[self.gate_index].target)
            if backwards:
                raise Exception("backwards unexpected on gate cross")
            if crossed_gate:
                self.gates[self.gate_index].missed = False
                elapsed_time = cross_gate_time - self.lap_start_time
                self.gates[self.gate_index].record_time_from_start(elapsed_time)
                # it's possible this throws an exception in the case this gate doesn't know
                # how long it takes to get to the end of the lap (perhaps it was missed on
                # all previous laps)
                try:
                    self.current_predicted_time = self.gates[self.gate_index].predict_lap(elapsed_time)
                    if self.gate_index % 10 == 0:
                        logger.info(
                            f"predicted lap time [gate = {self.gate_index}] = {self.current_predicted_time:.02f}")
                except IndexError:
                    pass
                self.gate_index += 1
            else:
                # see if we're nearer the next gate, if we are then we missed a gate
                this_pos = (this_gps.lat, this_gps.long)
                if self.gate_index < len(self.gates) - 1:
                    gate_dist = haversine(this_pos, self.gates[self.gate_index].target.midpoint, Unit.FEET)
                    next_gate_dist = haversine(this_pos, self.gates[self.gate_index + 1].target.midpoint,
                                               Unit.FEET)
                    if gate_dist > next_gate_dist:
                        logger.info(f"missed gate {self.gate_index}!!!")
                        self.gates[self.gate_index].missed = True
                        self.gate_index += 1

    def _update_gate_time_to_finish(self, last_lap_time):
        mins = int(last_lap_time / 60)
        secs = int(last_lap_time % 60)
        logger.debug(f"lap completed in {mins:02d}:{secs:02d} ... updating gates")
        if last_lap_time > len(self.gates) * 10 + 30:
            logger.warning(f"lap discarded as it's too slow")
            return
        for g in self.gates:
            g.record_lap_time(last_lap_time)

    def _determine_gates(self, target_distance):
        # after the breadcrumbing lap, see if we have a dataset already .. if we do,
        # then switch to use that
        matched = [g for g in self.gate_verifiers if g.is_match()]
        if not matched:
            return
        close = [g for g in matched if (abs(target_distance - g.get_distance_feet()) * 100 / target_distance) < 5]
        # sort by recent time
        close.sort(key=lambda a: a.get_timestamp(), reverse=True)
        # take the best match if it's less than 5% error. The 5% comes from pretending to breadcrumb
        # 100 laps at sonoma and measuring the actual observed variance. It was never more than 3%
        if close:
            self.gates = close[0].gates
        # reclaim the memory
        self.gate_verifiers = None

class DrsApproachPredictor(EventHandler):

    last_gps: Optional[GpsPos]

    def __init__(self, drs_gates: Gates):
        # might want to subclass gates or targets for this
        self.gates: Gates = drs_gates

    def update_position(self, lat, long, heading, time):
        # update the stored position
        # if about to cross a DRS line then emit an event predicting the cross
        # we will need to know from a gate whether it is a down or up gate (or store speed data so we know its faster or slower)
        # or just receive accel decel data and you know
        pass

