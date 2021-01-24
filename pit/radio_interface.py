from pit.event_defs import (
    RaceStatusEvent,
    LapCompletedEvent,
    PittingEvent,
    PingEvent,
    TelemetryEvent
)
from shared.events import EventHandler
from shared.generated.messages_pb2 import (
    RaceStatus,
    RacePosition,
    EnteringPits,
    Ping,
    CarTelemetry
)
from shared.radio import Radio
from threading import Thread
import logging

logger = logging.getLogger(__name__)


class RadioInterface(Thread, EventHandler):

    def __init__(self, radio:Radio):
        Thread.__init__(self, daemon=True)
        self.radio = radio
        RaceStatusEvent.register_handler(self)
        LapCompletedEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == RaceStatusEvent:
            self.send_race_status(**kwargs)

        if event == LapCompletedEvent:
            self.send_lap_completed(**kwargs)

    def run(self):
        while True:
            item = self.radio.receive_queue.get()
            logger.info("received : {}".format(item.__repr__()))
            self.radio.receive_queue.task_done()
            self.convert_to_event(item)

    def send_race_status(self, flag=""):
        logger.info("race status changed to {}".format(flag))
        status = RaceStatus()
        status.flagStatus = RaceStatus.RaceFlagStatus.UNKNOWN
        try:
            # this can fail with an empty string, in which case it remains
            # set to UNKNOWN
            status.flagStatus = RaceStatus.RaceFlagStatus.Value(flag.upper())
        except ValueError:
            pass
        self.radio.send_async(status)

    def send_lap_completed(self, car="", position=0, laps=0, ahead=None, gap="" ):
        logger.info("car: {} completed lap {} in pos {}".format(car, laps, position))
        pos = RacePosition()
        pos.car_number = car
        pos.position = position
        pos.lap_count = laps
        if ahead:
            pos.car_ahead.car_number = ahead
            pos.car_ahead.gap_text = gap
        self.radio.send_async(pos)

    def convert_to_event(self, proto_msg):
        if type(proto_msg) == EnteringPits:
            PittingEvent.emit(car=proto_msg.sender)
            return
        elif type(proto_msg) == CarTelemetry:
            TelemetryEvent.emit(car=proto_msg.sender,
                                ts=proto_msg.timestamp,
                                coolant_temp=proto_msg.coolant_temp,
                                lap_count=proto_msg.lap_count,
                                last_lap_time=proto_msg.last_lap_time,
                                last_lap_fuel=proto_msg.last_lap_fuel_usage,
                                fuel_percent=proto_msg.fuel_remaining_percent)
        elif type(proto_msg) == Ping:
            PingEvent.emit(car=proto_msg.sender, ts=proto_msg.timestamp)
        else:
            logger.error("unknown radio message {}".format(type(proto_msg)))
