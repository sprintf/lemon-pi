
from gps_reader import GpsReader
import logging
from movement_listener import MovementListener

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    MovementListener()
    tracker = GpsReader()
    tracker.start()