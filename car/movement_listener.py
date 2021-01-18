
from car.events import EventHandler, MovingEvent, NotMovingEvent, CarStoppedEvent
from haversine import haversine, Unit
import logging
import time

logger = logging.getLogger(__name__)


class MovementListener(EventHandler):

    def __init__(self):
        self.car_stopped = None
        self.moving = None
        self.last_lat_long = None
        self.bounding_box = None
        self.initial_stationary_time = None
        self._reset_(moving=False)
        MovingEvent.register_handler(self)
        NotMovingEvent.register_handler(self)

    def _reset_(self, moving=False):
        self.car_stopped = None
        self.moving = moving
        self.last_lat_long = None
        self.bounding_box = None
        self.initial_stationary_time = None

    def handle_event(self, event, speed=0, lat_long=(0, 0)):
        if event == MovingEvent:
            logger.debug("moving, speed = {}".format(speed))
            self._reset_(moving=True)
        if event == NotMovingEvent:
            if self.last_lat_long is None:
                self.initial_stationary_time = time.time()
            drift_radius_feet = self.update_bounding_box(lat_long)
            logger.debug("drift area = {}".format(drift_radius_feet))
            if drift_radius_feet > 20:
                self._reset_(moving=True)
            else:
                self.last_lat_long = lat_long
                if not self.car_stopped and time.time() - self.initial_stationary_time > 10:
                    CarStoppedEvent.emit()
                    self.car_stopped = True

    # update the bounding box and return the size of the box
    def update_bounding_box(self, lat_long):
        if self.bounding_box is None:
            self.bounding_box = (lat_long, lat_long)
            return 0
        self.bounding_box = ((min(self.bounding_box[0][0], lat_long[0]), min(self.bounding_box[0][1], lat_long[1])),
                             (max(self.bounding_box[1][0], lat_long[0]), max(self.bounding_box[1][1], lat_long[1])))
        drift_radius = int(haversine(self.bounding_box[0], self.bounding_box[1], Unit.FEET))
        return drift_radius


