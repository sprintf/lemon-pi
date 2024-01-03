
# functions
# do nothing if arduino is not connected
import json
import logging
import os
import threading
import time
from typing import Optional

import serial
from haversine import haversine, Unit

from lemon_pi.car.display_providers import DRSProvider
from lemon_pi.car.event_defs import DRSApproachEvent, CompleteLapEvent, LeaveTrackEvent
from lemon_pi.car.geometry import heading_between_lat_long, get_point_on_heading
from lemon_pi.car.gps_geometry import will_cross_line
from lemon_pi.car.gps_reader import GpsReader
from lemon_pi.car.target import Target
from lemon_pi.car.updaters import PositionUpdater
from lemon_pi.shared.data_provider_interface import GpsPos
from lemon_pi.shared.events import EventHandler
from lemon_pi.shared.usb_detector import UsbDetector, UsbDevice

logger = logging.getLogger(__name__)


class DrsController(DRSProvider):

    enabled = False
    activated = False
    future_activation: Optional[threading.Timer] = None
    serial_connection = None

    def __init__(self):
        if UsbDetector.detected(UsbDevice.ARDUINO):
            self.enabled = True
            # register for events ..
            LeaveTrackEvent.register_handler(self)
            DRSApproachEvent.register_handler(self)
            self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)

    def start(self):
        self.receive_thread.start()

    def is_drs_available(self) -> bool:
        return self.enabled

    def is_drs_activated(self) -> bool:
        return self.activated

    def handle_event(self, event, **kwargs):
        if event == DRSApproachEvent:
            delay = kwargs['delay']
            if delay < 0:
                return
            logger.info(f"calling with {delay} {kwargs['activated']}")
            # do we have a timer set?
            # if yes then cancel it, and set again based on time until we cross now
            if self.future_activation:
                self.future_activation.cancel()
            self.future_activation = threading.Timer(delay, self.activate_drs, args=[kwargs['activated']])
            self.future_activation.start()
        if event == LeaveTrackEvent:
            self.activate_drs(True)

    def activate_drs(self, activate: bool):
        self.activated = activate
        self.connect_arduino()
        if activate:
            self.serial_connection.write("up".encode("utf-8"))
            logger.info("DRS activated on Arduino")
        else:
            self.serial_connection.write("down".encode("utf-8"))
            logger.info("DRS deactivated on Arduino")

    def connect_arduino(self):
        arduino = UsbDetector.get(UsbDevice.ARDUINO)
        if not self.serial_connection:
            self.serial_connection = serial.Serial(arduino, baudrate=115200, timeout=2)
        if not self.serial_connection.isOpen():
            self.serial_connection.open()

    def receive_loop(self):
        self.connect_arduino()
        while True:
            try:
                response = self.serial_connection.readline()
                if len(response):
                    logger.info(f"arduino >> {response}")
            except serial.SerialException:
                logger.info("exception from arduino comms, closing connection")
                self.serial_connection.close()
                time.sleep(30)
                self.connect_arduino()


class DrsGate:
    
    def __init__(self, lat1, long1, lat2, long2, name, activation):
        self.target: Target = Target(name, (lat1, long1), (lat2, long2), target_heading=-1)
        self.activation: bool = activation
        self.time_adjust: float = 0.0
    

class DrsDataLoader:

    def __init__(self):
        self.trackDrsZones: {str, [DrsGate]} = {}

    def get_drs_activation_zones(self, track_code: str):
        if track_code in self.trackDrsZones:
            return self.trackDrsZones[track_code]
        return None

    def read_file(self, filename: str):
        with open(filename) as f:
            d = json.load(f)
            for e in d:
                self.trackDrsZones[e["track"]] = self.build_gates(e["gates"])

    @staticmethod
    def build_gates(gates):
        result = []
        for g in gates:
            activation = g["activation"]
            if 'desc' in g:
                name = g["desc"]
            else:
                if activation:
                    name = f"drs-on-{len(result)}"
                else:
                    name = f"drs-off-{len(result)}"
            p = g["points"]
            heading = heading_between_lat_long((p[0][0], p[0][1]), (p[1][0], p[1][1]))
            # widen up the gates because the heading is laggy on drs
            wider_point_1 = get_point_on_heading((p[0][0], p[0][1]), heading + 180, d=0.01)
            wider_point_2 = get_point_on_heading((p[1][0], p[1][1]), heading, d=0.01)
            result.append(DrsGate(wider_point_1[0], wider_point_1[1],
                                  wider_point_2[0], wider_point_2[1],
                                  name, activation))
        return result


class DrsPositionTracker(PositionUpdater, EventHandler):

    def __init__(self, gates: [DrsGate]):
        self.gates = gates
        self.gate_index = 0
        CompleteLapEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == CompleteLapEvent:
            self.gate_index = 0

    def update_position(self, lat: float, long: float, heading: float, tstamp: float, speed: int) -> None:
        here = GpsPos(lat, long, heading, speed, tstamp)
        gate = self.gates[self.gate_index]
        target = gate.target
        (cross, est_time, backwards) = will_cross_line(here, target)
        next_gate = self.gate_index + 1
        if next_gate >= len(self.gates):
            next_gate = 0
        if cross:
            logger.info(f"will cross line {target.name} at {est_time}")
            self.gate_index = next_gate
            # todo : take the timeadjustment into account if there is one
            DRSApproachEvent.emit(delay=(est_time - tstamp),
                                  activated=gate.activation,
                                  gate=gate)
        else:
            # if we're closer to the next gate then we're in trouble .. we missed one
            gate_dist = haversine((lat, long), target.midpoint, Unit.FEET)
            next_gate_dist = haversine((lat, long), self.gates[next_gate].target.midpoint, Unit.FEET)
            if next_gate_dist < 200 and next_gate_dist <= gate_dist:
                logger.info(
                    f"missed gate {target.name} !!! distance to it is {gate_dist} ft "
                    f"but next gate is {next_gate_dist} ft")
                self.gate_index = next_gate


if __name__ == "__main__":

    if "SETTINGS_MODULE" not in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_car"

    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    UsbDetector.init()

    drsZones = DrsDataLoader()
    drsZones.read_file("resources/drs_zones.json")
    test_gates = drsZones.trackDrsZones["test1"]

    drs_tracker = DrsPositionTracker(test_gates)

    tracker = GpsReader()
    tracker.call_gpsctl()
    tracker.register_position_listener(drs_tracker)
    tracker.run()
