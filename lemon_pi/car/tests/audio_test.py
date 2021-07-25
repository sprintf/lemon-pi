
import unittest
from unittest.mock import Mock, patch

from lemon_pi.car.audio import Audio
from lemon_pi.car.event_defs import ButtonPressEvent, CompleteLapEvent


class TestAudio(unittest.TestCase):

    @patch('pygame.mixer.Sound')
    def test_lap_times(self, m_sound):
        audio = Audio()
        audio.announce = Mock()
        audio.announce_lap_time(60.0)
        audio.announce.assert_called_with('1 minute dead')

        audio.announce_lap_time(120.1)
        audio.announce.assert_called_with('2 minutes dead')

        audio.announce_lap_time(122.1)
        audio.announce.assert_called_with('2. 02')

        audio.announce_lap_time(198.1)
        audio.announce.assert_called_with('3. 18')

    @patch('pygame.mixer.Sound')
    def test_button_press(self, m_sound):
        audio = Audio()
        audio.play_click = Mock()
        ButtonPressEvent.emit(button=0)
        audio.play_click.assert_called_once()

    @patch('pygame.mixer.Sound')
    def test_lap_completed(self, m_sound):
        audio = Audio()
        CompleteLapEvent.emit(lap_time=54.252)
        self.assertEqual(1, audio.queue.qsize())
        audio.engine.say = Mock()
        audio.engine.runAndWait = Mock()
        audio.run_once()
        audio.engine.say.assert_called_with("54 seconds")
        audio.engine.runAndWait.assert_called_once()

    def test_number_announcement(self):
        self.assertEqual("one five six", Audio._car_number_to_audio("156"))
        self.assertEqual("nine nine", Audio._car_number_to_audio("99"))
        self.assertEqual("double O. seven", Audio._car_number_to_audio("007"))
        self.assertEqual("0", Audio._car_number_to_audio("0"))
        self.assertEqual("10", Audio._car_number_to_audio("10"))
        self.assertEqual("100", Audio._car_number_to_audio("100"))
        self.assertEqual("seven O. seven", Audio._car_number_to_audio("707"))
        self.assertEqual("11b", Audio._car_number_to_audio("11b"))





