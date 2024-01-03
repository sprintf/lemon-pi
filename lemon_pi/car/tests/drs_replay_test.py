import csv
import unittest

from lemon_pi.car.drs_controller import DrsDataLoader, DrsPositionTracker, DrsGate
from lemon_pi.car.event_defs import DRSApproachEvent
from lemon_pi.shared.events import EventHandler


class EventHelper(EventHandler):

    def __init__(self, gates: [DrsGate]):
        self.gates = gates
        self.event_count = 0
        self.total_gates_hit = 0
        self.total_gates_missed = 0
        self.gates_hit = set()

    def lap_completed(self):
        self.event_count = 0
        all_gates = set(f.target.name for f in self.gates)
        missed_gates = all_gates.difference(self.gates_hit)
        print(f"missed gates = {missed_gates}")
        self.total_gates_missed += len(missed_gates)
        self.total_gates_hit += (len(all_gates) - len(missed_gates))
        self.gates_hit = set()


    def handle_event(self, e, **kwargs):
        self.event_count += 1
        if 'gate' in kwargs:
            gate = kwargs['gate']
            self.gates_hit.add(gate.target.name)


class DrsReplayTest(unittest.TestCase):

    def test_processing_sonoma(self):
        loader = DrsDataLoader()
        loader.read_file("resources/drs_zones.json")
        snma_drs_zones = loader.get_drs_activation_zones("snma")

        event_handler = EventHelper(snma_drs_zones)
        DRSApproachEvent.register_handler(event_handler)

        tracker = DrsPositionTracker(snma_drs_zones)

        with open("resources/test/gps-2022-03-12.csv") as csvfile:
            rows = csv.reader(csvfile)
            current_lap = 0
            for row in rows:
                tstamp = float(row[1])
                lap = int(row[2])
                lat = float(row[3])
                long = float(row[4])
                speed = int(row[5])
                heading = int(row[6])

                # if lap < 91 or lap == 999:
                #     current_lap = lap
                #     continue

                if lap != current_lap:
                    event_handler.lap_completed()
                    current_lap = lap
                    print(f"starting lap {current_lap}")
                    # print(f"detected {event_handler.event_count} DRS zones on last lap")

                tracker.update_position(lat, long, heading, tstamp, speed)

        print(f"total gates hit = {event_handler.total_gates_hit}")
        print(f"total gates missed = {event_handler.total_gates_missed}")

    def test_processing_thunderhill(self):
        loader = DrsDataLoader()
        loader.read_file("resources/drs_zones.json")
        thil_drs_zones = loader.get_drs_activation_zones("thil")

        event_handler = EventHelper(thil_drs_zones)
        DRSApproachEvent.register_handler(event_handler)

        tracker = DrsPositionTracker(thil_drs_zones)

        with open("resources/test/gps-2023-05-27.csv") as csvfile:
            rows = csv.reader(csvfile)
            current_lap = 0
            for row in rows:
                tstamp = float(row[1])
                lap = int(row[2])
                lat = float(row[3])
                long = float(row[4])
                speed = int(row[5])
                heading = int(row[6])

                if lap < 91 or lap == 999:
                    current_lap = lap
                    continue

                if lap != current_lap:
                    event_handler.lap_completed()
                    current_lap = lap
                    print(f"starting lap {current_lap}")
                    # print(f"detected {event_handler.event_count} DRS zones on last lap")

                tracker.update_position(lat, long, heading, tstamp, speed)

        print(f"total gates hit = {event_handler.total_gates_hit}")
        print(f"total gates missed = {event_handler.total_gates_missed}")