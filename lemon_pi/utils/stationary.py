
from lemon_pi.car.gps_reader import GpsReader
import logging
from lemon_pi.car.movement_listener import MovementListener

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    MovementListener()
    tracker = GpsReader()
    tracker.start()