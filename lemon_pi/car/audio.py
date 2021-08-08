import subprocess

import pyttsx3
import logging
from queue import Queue
from threading import Thread

from lemon_pi.car.event_defs import ButtonPressEvent, CompleteLapEvent, AudioAlarmEvent, RacePositionEvent
from lemon_pi.shared.events import EventHandler

logger = logging.getLogger(__name__)


class Audio(Thread, EventHandler):

    number_to_text = {
        '0' : "O.",
        '1' : "one",
        '2' : "two",
        '3' : "three",
        '4' : "four",
        '5' : "five",
        '6' : "six",
        '7' : "seven",
        '8' : "eight",
        '9' : "nine"
    }

    def __init__(self):
        Thread.__init__(self, daemon=True)
        self.engine = pyttsx3.init()
        self.engine.setProperty('volume', 1.0)
        self.queue = Queue()
        self.click_sound = 'resources/sounds/click.wav'
        ButtonPressEvent.register_handler(self)
        CompleteLapEvent.register_handler(self)
        AudioAlarmEvent.register_handler(self)
        RacePositionEvent.register_handler(self)

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
            self.announce_race_position(**kwargs)
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
        self.engine.runAndWait()
        self.queue.task_done()

    def announce(self, message:str):
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

    def announce_race_position(self, pos=0, pos_in_class=0, car_ahead="", gap=""):
        if pos == 1:
            return

        if pos_in_class == pos:
            self.announce("You are in P {pos}")
        else:
            self.announce(f"You are P {pos_in_class} in class, P {pos} overall")

        if gap and car_ahead:
            car_number = Audio._car_number_to_audio(car_ahead)
            self.announce(f"Car {car_number} is {gap} ahead")

    @staticmethod
    def _car_number_to_audio(car_number:str):
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

