import time
import unittest
from unittest.mock import patch, MagicMock

from lemon_pi.car.drs_controller import DrsDataLoader, DrsController, DrsPositionTracker, DrsGate
from lemon_pi.car.event_defs import DRSApproachEvent
from lemon_pi.car.gps_geometry import will_cross_line
from lemon_pi.car.target import Target
from lemon_pi.car.track import TrackLocation, read_tracks
from lemon_pi.shared.data_provider_interface import GpsPos


class DrsFileLoadTest(unittest.TestCase):

    def test_loading_file(self):
        tracks: [TrackLocation] = read_tracks()
        track_codes: set[str] = set(t.code for t in tracks)
        loader = DrsDataLoader()
        loader.read_file("resources/drs_zones.json")
        for code, gates in loader.trackDrsZones.items():
            self.assertTrue(code in track_codes)
            # must be an even number of gates
            self.assertTrue(len(gates) % 2 == 0)
            for gate in gates:
                # we can't have more than 1s time adjust
                self.assertTrue(abs(gate.time_adjust) <= 1)


class DrsTracker(unittest.TestCase):

    @patch("lemon_pi.car.drs_controller.will_cross_line", return_value=(True, 1000, False))
    @patch("lemon_pi.car.event_defs.DRSApproachEvent.emit")
    def test_increased_delay(self, drs_event, _):
        gate1 = DrsGate(0.99, 0.99, 1.001, 1.001, "test", True, +2)
        gates = [gate1]
        d = DrsPositionTracker(gates)
        d.update_position(0.9990, 0.9990, 45, 1000, 100)
        # we're asserting the delay is 2, which was specified in the gate
        drs_event.assert_called_with(delay=2, activated=True, gate=gate1)

    @patch("lemon_pi.car.drs_controller.will_cross_line", return_value=(True, 1000, False))
    @patch("lemon_pi.car.event_defs.DRSApproachEvent.emit")
    def test_decreased_delay(self, drs_event, _):
        gate1 = DrsGate(0.99, 0.99, 1.001, 1.001, "test", True, -0.5)
        gates = [gate1]
        d = DrsPositionTracker(gates)
        d.update_position(0.9990, 0.9990, 45, 1000, 100)
        # we're asserting the delay is -0.5, which was specified in the gate
        drs_event.assert_called_with(delay=-0.5, activated=True, gate=gate1)


class DrsLineDetectionTest(unittest.TestCase):

    def test_arlington_line_cross(self):
        t = Target("test", (37.92566471254159, -122.29457266858205), (37.92572183777478, -122.29442380598172))
        p2 = GpsPos(37.92574905126326, -122.29456804308042, 160, 35, 50000)
        (cross, est_time, backwards) = will_cross_line(p2, t)
        self.assertTrue(cross)
        self.assertAlmostEqual(50000.826, est_time, 2)
        self.assertFalse(backwards)


class DrsControllerTest(unittest.TestCase):

    @patch('lemon_pi.shared.usb_detector.UsbDetector.detected', return_value=False)
    def test_not_available(self, _):
        d = DrsController()
        self.assertFalse(d.is_drs_available())

    @patch('lemon_pi.shared.usb_detector.UsbDetector.detected', return_value=True)
    def test_available(self, _):
        d = DrsController()
        self.assertTrue(d.is_drs_available())

    @patch('lemon_pi.shared.usb_detector.UsbDetector.detected', return_value=True)
    def test_handling_single_event(self, _):
        d = DrsController()
        d.activate_drs = MagicMock()
        d.handle_event(DRSApproachEvent, delay=0.1, activated=True)
        d.activate_drs.assert_not_called()
        time.sleep(0.2)
        d.activate_drs.assert_called_once_with(True)
        d.handle_event(DRSApproachEvent, delay=0.1, activated=False)
        time.sleep(0.2)
        d.activate_drs.assert_called_with(False)

    @patch('lemon_pi.shared.usb_detector.UsbDetector.detected', return_value=True)
    def test_handling_sequence_of_events(self, _):
        d = DrsController()
        d.activate_drs = MagicMock()
        d.handle_event(DRSApproachEvent, delay=0.2, activated=True)
        d.activate_drs.assert_not_called()
        d.handle_event(DRSApproachEvent, delay=0.1, activated=True)
        time.sleep(0.5)
        d.activate_drs.assert_called_once_with(True)
