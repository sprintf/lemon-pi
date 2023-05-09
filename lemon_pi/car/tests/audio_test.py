
import unittest
from unittest.mock import Mock

from lemon_pi.car.audio import Audio
from lemon_pi.car.event_defs import ButtonPressEvent, CompleteLapEvent, RacePositionEvent, DriverMessageEvent

from python_settings import settings
import lemon_pi.config.test_settings as my_local_settings

if not settings.configured:
    settings.configure(my_local_settings)

class TestAudio(unittest.TestCase):

    def test_lap_times(self):
        audio = Audio()
        audio.announce = Mock()
        audio.announce_lap_time(60.0)
        audio.announce.assert_called_with('1 minute dead')

        audio.announce_lap_time(120.1)
        audio.announce.assert_called_with('2 minutes dead')

        audio.announce_lap_time(122.1)
        audio.announce.assert_called_with('2. O. 2')

        audio.announce_lap_time(198.1)
        audio.announce.assert_called_with('3. 18')

    def test_button_press(self):
        audio = Audio()
        audio.play_click = Mock()
        ButtonPressEvent.emit(button=0)
        audio.play_click.assert_called_once()

    def test_lap_completed(self):
        audio = Audio()
        CompleteLapEvent.emit(lap_time=54.252, lap_count=5)
        self.assertEqual(1, audio.queue.qsize())
        audio.engine.say = Mock()
        audio.engine.runAndWait = Mock()
        audio.run_once()
        audio.engine.say.assert_called_with("54 seconds")
        audio.engine.runAndWait.assert_called_once()

    def test_race_position(self):
        audio = Audio()
        audio.engine.say = Mock()
        audio.engine.runAndWait = Mock()
        audio.last_race_announcement_time = 0
        RacePositionEvent.emit(gap_to_front=0.0, pos=3)
        self.assertEqual(1, audio.queue.qsize())
        audio.run_once()
        audio.last_race_announcement_time = 0
        RacePositionEvent.emit(gap_to_front=60 * 31, pos=3)
        self.assertEqual(1, audio.queue.qsize())
        audio.run_once()
        audio.last_race_announcement_time = 0
        RacePositionEvent.emit(gap_to_front=108.5, pos=3)
        self.assertEqual(2, audio.queue.qsize())
        audio.run_once()
        audio.run_once()
        audio.engine.say.assert_called_with("Gap to front is 108 seconds")

    def test_gap_to_front_delta(self):
        audio = Audio()
        audio.engine.say = Mock()
        audio.engine.runAndWait = Mock()
        audio.last_race_announcement_time = 0
        RacePositionEvent.emit(gap_to_front=15.5, gap_to_front_delta=-1.5, pos=3)
        self.assertEqual(2, audio.queue.qsize())
        audio.run_once()
        audio.run_once()
        audio.engine.say.assert_called_with("Gap to front decreased by 1 seconds")

    def test_number_announcement(self):
        self.assertEqual("one five six", Audio._car_number_to_audio("156"))
        self.assertEqual("nine nine", Audio._car_number_to_audio("99"))
        self.assertEqual("double O. seven", Audio._car_number_to_audio("007"))
        self.assertEqual("0", Audio._car_number_to_audio("0"))
        self.assertEqual("10", Audio._car_number_to_audio("10"))
        self.assertEqual("100", Audio._car_number_to_audio("100"))
        self.assertEqual("seven O. seven", Audio._car_number_to_audio("707"))
        self.assertEqual("11b", Audio._car_number_to_audio("11b"))

    def test_driver_message(self):
        audio = Audio()
        DriverMessageEvent.emit(text="pit in 3 laps", audio=True)
        self.assertEqual(1, audio.queue.qsize())
        audio.engine.say = Mock()
        audio.engine.runAndWait = Mock()
        audio.run_once()
        audio.engine.say.assert_called_with("pit in 3 laps")

    def test_driver_message_no_audio(self):
        audio = Audio()
        DriverMessageEvent.emit(text="pit in 3 laps", audio=False)
        self.assertEqual(0, audio.queue.qsize())

    def test_driver_message_no_audio_flag(self):
        audio = Audio()
        DriverMessageEvent.emit(text="pit in 3 laps")
        self.assertEqual(0, audio.queue.qsize())






