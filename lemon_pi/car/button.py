
import RPi.GPIO as GPIO
from event_defs import ButtonPressEvent
import time

from lemon_pi.shared.events import EventHandler

INPUT_PIN = 10

class Button(EventHandler):

    def __init__(self):
        self.text = None
        self.ack_timeout = None

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(INPUT_PIN, GPIO.RISING, callback=self.button_handler)

    def handle_event(self, event, timeout=0, **kwargs):
        self.ack_timeout = timeout
        self.event = event
        self.kwargs = kwargs

    def button_handler(self):
        if self.ack_timeout > time.time() and self.text:
            ButtonPressEvent.emit(button=0, event=self.event, **self.kwargs)

