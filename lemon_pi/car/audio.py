import platform
import subprocess
import time

import pyttsx4
import logging
from queue import Queue
from threading import Thread

from lemon_pi.car.event_defs import ButtonPressEvent, CompleteLapEvent, AudioAlarmEvent, RacePositionEvent, \
    DriverMessageEvent
from lemon_pi.shared.events import EventHandler

from python_settings import settings


logger = logging.getLogger(__name__)


def get_speech_driver():
    os_type = platform.system()
    if os_type == 'Linux':
        return 'espeak'
    elif os_type == 'Darwin':
        return 'dummy'
    else:
        raise Exception("unknown platform: {}".format(os_type))


class Audio(Thread, EventHandler):

    number_to_text = {
        '0': "O.",
        '1': "one",
        '2': "two",
        '3': "three",
        '4': "four",
        '5': "five",
        '6': "six",
        '7': "seven",
        '8': "eight",
        '9': "nine"
    }

    def __init__(self):
        Thread.__init__(self, daemon=True)
        self.engine = pyttsx4.init(get_speech_driver())
        self.engine.setProperty('volume', 1.0)
        # set 150 words per minute as the rate
        self.engine.setProperty('rate', 150)
        # on Darwin we seem to need this... on RPi it blocks
        # self.engine.startLoop()
        self.queue = Queue()
        self.click_sound = 'resources/sounds/click.wav'
        self.last_race_announcement_time = 0
        ButtonPressEvent.register_handler(self)
        CompleteLapEvent.register_handler(self)
        AudioAlarmEvent.register_handler(self)
        RacePositionEvent.register_handler(self)
        DriverMessageEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == ButtonPressEvent:
            self.play_click()
            return
        if event == CompleteLapEvent:
            self.announce_lap_time(**kwargs)
            return
        if event == AudioAlarmEvent:
            self.announce_alarm(**kwargs)
            return
        if event == RacePositionEvent:
            # upon reconnect we can get a slew of these, we'll avoid the annoyance
            if time.time() - self.last_race_announcement_time < 60:
                return
            self.announce_race_position(**kwargs)
            self.last_race_announcement_time = time.time()
            return
        if event == DriverMessageEvent:
            if 'audio' in kwargs.keys() and kwargs['audio']:
                self.announce(kwargs["text"])
            return

    def run(self) -> None:
        while True:
            try:
                self.run_once()
            except Exception:
                logger.exception("got an exception in audio")

    def run_once(self):
        msg = self.queue.get()
        logger.info(f"announcing '{msg}'")
        self.engine.say(msg)
        # on Darwin this crashes the whole app, on RPi it seems fine.
        self.engine.runAndWait()
        self.queue.task_done()

    def announce(self, message: str):
        # queue up the announcement
        self.queue.put(message)

    def play_click(self):
        result = subprocess.run(["aplay", self.click_sound],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error("failed to play click sound")

    def announce_lap_time(self, lap_time=1.0, lap_count=0):
        minutes = int(lap_time / 60)
        seconds = int(lap_time % 60)
        plural = "s" if minutes > 1 else ""
        if minutes > 0:
            if seconds == 0:
                self.announce(f"{minutes} minute{plural} dead")
            elif seconds < 10:
                self.announce(f"{minutes}. O. {seconds}")
            else:
                self.announce(f"{minutes}. {seconds}")
        else:
            self.announce(f"{seconds} seconds")

    def announce_alarm(self, message=""):
        # todo : play an alert tone
        # todo : play it now ... if poss
        self.announce(f"Danger! {message}")

    def announce_race_position(self, pos=0, pos_in_class=0, car_ahead="", gap="",
                               gap_to_front=0.0, gap_to_front_delta=0.0, lap_count=0):
        if pos == 1:
            return

        if pos_in_class == pos or pos_in_class == 0:
            self.announce(f"You are in P {pos}")
        else:
            self.announce(f"You are P {pos_in_class} in class, P {pos} overall")

        if gap and car_ahead:
            car_number = Audio._car_number_to_audio(car_ahead)
            gap_words, extra = self._gap_to_audio(gap)
            self.announce(f"Car {car_number} is {gap_words} ahead {extra}")

        if settings.AUDIO_ANNOUNCE_GAP_TO_FRONT:
            if gap_to_front_delta and gap_to_front < 60 * 30:
                if gap_to_front_delta > 0 and gap_to_front_delta < 10:
                    self.announce(f"Gap to front increased by {int(gap_to_front_delta)} seconds")
                if gap_to_front_delta < 0:
                    self.announce(f"Gap to front decreased by {int(-gap_to_front_delta)} seconds")
            else:
                if gap_to_front > 0.0 and gap_to_front < 60 * 30:
                    # while we're within 30 minutes of the front, announce our gap to the front
                    self.announce(f"Gap to front is {int(gap_to_front)} seconds")

    @staticmethod
    def _car_number_to_audio(car_number: str):
        # car number that are tens and hundreds should be pronounced as-is
        if car_number.endswith("0"):
            return car_number
        # james bond style logic
        if car_number.startswith("00"):
            return "double O. " + Audio._car_number_to_audio(car_number[2])
        # for other numbers we want to turn them into a sequence of their digits
        # e.g. 199 would not be "one hundred and ninety nine" it would be "one nine nine"
        try:
            result = ""
            for digit in car_number:
                result += Audio.number_to_text[digit] + " "
            return result.strip()
        except KeyError:
            return car_number

    @staticmethod
    def _gap_to_audio(gap: str) -> (str, str):
        if gap == "-":
            return "", ""

        if gap.endswith("L(p)"):
            gap = gap[:-4]
            return f"{gap} laps", "and is in the pits"

        if gap.endswith("L"):
            return f"{gap}aps", ""

        if gap.endswith("s"):
            return f"{gap}econds", ""

        return gap, ""
