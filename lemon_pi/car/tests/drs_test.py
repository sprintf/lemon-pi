import time
import unittest
from unittest.mock import patch, MagicMock

from lemon_pi.car.drs_controller import DrsDataLoader, DrsController
from lemon_pi.car.event_defs import DRSApproachEvent
from lemon_pi.car.gps_geometry import will_cross_line
from lemon_pi.car.target import Target
from lemon_pi.shared.data_provider_interface import GpsPos


class DrsFileLoadTest(unittest.TestCase):

    def test_loading_file(self):
        DrsDataLoader().read_file("resources/drs_zones.json")


class DrsLineDetectionTest(unittest.TestCase):

    def test_arlington_line_cross(self):
        t = Target("test", (37.92566471254159, -122.29457266858205), (37.92572183777478, -122.29442380598172))
        p2 = GpsPos(37.92574905126326, -122.29456804308042, 160, 35, 50000)
        (cross, est_time, backwards) = will_cross_line(p2, t)
        self.assertTrue(cross)
        self.assertAlmostEqual(50000.682, est_time, 2)
        self.assertFalse(backwards)


class DrsControllerTest(unittest.TestCase):

    @patch('lemon_pi.shared.usb_detector.UsbDetector.detected', return_value=False)
    def test_not_available(self, usb):
        d = DrsController()
        self.assertFalse(d.is_drs_available())

    @patch('lemon_pi.shared.usb_detector.UsbDetector.detected', return_value=True)
    def test_available(self, usb):
        d = DrsController()
        self.assertTrue(d.is_drs_available())

    @patch('lemon_pi.shared.usb_detector.UsbDetector.detected', return_value=True)
    def test_handling_single_event(self, usb):
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
    def test_handling_sequence_of_events(self, usb):
        d = DrsController()
        d.activate_drs = MagicMock()
        d.handle_event(DRSApproachEvent, delay=0.2, activated=True)
        d.activate_drs.assert_not_called()
        d.handle_event(DRSApproachEvent, delay=0.1, activated=True)
        time.sleep(0.5)
        d.activate_drs.assert_called_once_with(True)
