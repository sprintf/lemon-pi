
import RPi.GPIO as GPIO
from lemon_pi.car.event_defs import ButtonPressEvent
import logging

INPUT_PIN = 10

logger = logging.getLogger(__name__)

class Button():

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # might want to try bouncetime=200 if its very bouncy
        GPIO.add_event_detect(INPUT_PIN, GPIO.RISING, callback=self.button_handler, bouncetime=350)

    def button_handler(self, channel):
        logger.debug("button pressed")
        ButtonPressEvent.emit(button=0)


