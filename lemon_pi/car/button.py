
import RPi.GPIO as GPIO
from event_defs import ButtonPressEvent
from threading import Thread
import time

INPUT_PIN = 10


class Button(Thread):

    def __init__(self):
        Thread.__init__(self, daemon=True)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # might want to try bouncetime=200 if its very bouncy
        # GPIO.add_event_detect(INPUT_PIN, GPIO.RISING, callback=self.button_handler, bouncetime=200)

    def run(self):
        while True:
            GPIO.wait_for_edge(INPUT_PIN, GPIO.RISING)
            ButtonPressEvent.emit(button=0)
            time.sleep(0.2)
            print("handled button press")


