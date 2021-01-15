
import os
import logging
from logging.handlers import RotatingFileHandler
from python_settings import settings

from shared.radio import Radio


logger = logging.getLogger(__name__)
if not os.path.isdir("logs"):
    os.mkdir("logs")

handler = RotatingFileHandler("logs/lemon-pit.log",
                              maxBytes=10000000,
                              backupCount=10)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
handler.setLevel(logging.INFO)
logging.getLogger().addHandler(handler)

logger.info("Lemon-Pit : starting up")


logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "config.settings-pit"


def run():
    # start the radio thread
    radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY)
    radio.start()

    # wait for incoming messages, and log them as they arrive
    while True:
        # pluck incoming messages off the queue
        item = radio.receive_queue.pop()
        logger.info("received : {}".format(item.__repr__()))


if __name__ == "__main__":
    run()