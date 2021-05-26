from queue import Queue

from lemon_pi.pit.leaderboard import RaceOrder, CarPosition, PositionEnum
from lemon_pi.pit.event_defs import LapCompletedEvent, TargetTimeEvent
from lemon_pi.shared.events import EventHandler
from statistics import median
from threading import Thread
import time


# class whose job it is to emit helpful events around strategy
# It listens for the lap crossing event.
#
# This class runs in it's own thread because when the event arrives,
# there's a whole sequence of related events that come in over a short
# window of time, so it is not safe to query the data in the leaderboard
# until after the updates have all been applied
#
class StrategyAnalyzer(EventHandler, Thread):

    def __init__(self, leaderboard: RaceOrder, target_cars: [str]):
        Thread.__init__(self, daemon=True)
        self.leaderboard = leaderboard
        self.target_cars = target_cars
        self.next_lap_target = 0
        self.position_mode = PositionEnum.OVERALL
        self.analysis_queue = Queue()
        self.running = False
        LapCompletedEvent.register_handler(self)

    def set_position_mode(self, position_mode: PositionEnum):
        self.position_mode = position_mode

    def run(self):
        self.running = True
        while True:
            data = self.analysis_queue.get()

            # wait for the related events to all arrive
            time.sleep(0.5)
            self._do_handle_event(data['event'],
                                  car=data['car_number'])

    def handle_event(self, event, car="181", **kwargs):
        if event == LapCompletedEvent and car in self.target_cars:
            if self.running:
                self.analysis_queue.put({"event": event,
                                         "car_number": car,
                                         })
            else:
                # synchronous mode for testing
                self._do_handle_event(event, car)


    def _do_handle_event(self, event, car="181"):
        if event == LapCompletedEvent:
            if car in self.target_cars:
                self.next_lap_target = self.calc_target_time(car)
                TargetTimeEvent.emit(car=car, seconds=self.next_lap_target)

    def calc_target_time(self, car_number):
        car: CarPosition = self.leaderboard.lookup(car_number)
        if car:
            lap_times = []
            count = 0
            cursor: CarPosition = car.get_car_in_front(self.position_mode)
            while cursor and count < 10:
                count += 1
                lap_times.append(cursor.last_lap_time)
                cursor = cursor.get_car_in_front(self.position_mode)
            if count == 0:
                return car.last_lap_time
            if count == 1:
                # if only 1 car ahead then simplify to close 1s per lap
                return lap_times[0] - 1
            else:
                # print("in class position {} ({})".format(count + 1, car.class_position))
                # print("times ahead = {}".format(lap_times))
                # choose the median of the 10 cars ahead
                return median(lap_times)

    def get_target_time(self):
        return self.next_lap_target

