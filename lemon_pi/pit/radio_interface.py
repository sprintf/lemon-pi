from lemon_pi.pit.event_defs import (
    RaceStatusEvent,
    LapCompletedEvent,
    PittingEvent,
    PingEvent,
    TelemetryEvent,
    SendMessageEvent, RadioReceiveEvent, SendTargetTimeEvent, ResetFastLapEvent, SendFastLapResetEvent
)
from lemon_pi.shared.events import EventHandler
from lemon_pi.shared.generated.messages_pb2 import (
    EnteringPits,
    Ping,
    CarTelemetry,
    RaceFlagStatus,
    ToCarMessage
)
from lemon_pi.shared.radio import Radio
from python_settings import settings

from threading import Thread
import time
import logging

logger = logging.getLogger(__name__)


class RadioInterface(Thread, EventHandler):

    def __init__(self, radio: Radio):
        Thread.__init__(self, daemon=True)
        self.radio = radio
        RaceStatusEvent.register_handler(self)
        LapCompletedEvent.register_handler(self)
        SendMessageEvent.register_handler(self)
        SendTargetTimeEvent.register_handler(self)
        ResetFastLapEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == RaceStatusEvent:
            self.send_race_status(**kwargs)
            return

        if event == LapCompletedEvent:
            self.send_lap_completed(**kwargs)
            return

        if event == SendMessageEvent:
            self.send_driver_message(**kwargs)
            return

        if event == SendTargetTimeEvent:
            self.send_target_time(**kwargs)
            return

        if event == SendFastLapResetEvent:
            self.send_fast_lap_reset(**kwargs)
            return

    def run(self):
        while True:
            item = self.radio.receive_queue.get()
            logger.info("received : {}".format(item.__repr__()))
            self.radio.receive_queue.task_done()
            self.convert_to_event(item)
            RadioReceiveEvent.emit(car=item.sender)

    def send_race_status(self, flag=""):
        logger.info("race status changed to {}".format(flag))
        msg = ToCarMessage()
        msg.race_status.flag_status = self.set_flag_status(flag)
        self.radio.send_async(msg)

    @classmethod
    def set_flag_status(cls, flag):
        try:
            # this can fail with an empty string, in which case it remains
            # set to UNKNOWN
            return RaceFlagStatus.Value(flag.upper())
        except ValueError:
            pass
        return RaceFlagStatus.UNKNOWN

    def send_lap_completed(self, car="", position=0, class_position=0,
                           laps=0, ahead=None, gap="", last_lap_time=0, flag=""):
        logger.info("car: {} completed lap {} in pos {}({}) last = {}".
                    format(car, laps, position, class_position, last_lap_time))
        msg = ToCarMessage()
        msg.race_position.car_number = car
        msg.race_position.position = position
        msg.race_position.position_in_class = class_position
        msg.race_position.lap_count = laps
        msg.race_position.flag_status = self.set_flag_status(flag)
        if ahead:
            msg.race_position.car_ahead.car_number = ahead
            msg.race_position.car_ahead.gap_text = gap
        delayed_send = Thread(target=self.__delayed_send__, args=(msg, settings.RACE_DATA_SEND_DELAY_SEC))
        if settings.RACE_DATA_SEND_DELAY_SEC > 0:
            delayed_send.start()
        else:
            # run it in foreground for unittests
            delayed_send.run()

    def send_driver_message(self, car="", msg=""):
        wrapper = ToCarMessage()
        wrapper.message.text = msg
        wrapper.message.car_number = car
        self.radio.send_async(wrapper)

    def send_target_time(self, car="", target_time=2.0):
        wrapper = ToCarMessage()
        wrapper.set_target.car_number = car
        wrapper.set_target.target_lap_time = target_time
        self.radio.send_async(wrapper)

    def send_fast_lap_reset(self, car=""):
        wrapper = ToCarMessage()
        wrapper.reset_fast_lap.car_number = car
        self.radio.send_async(wrapper)

    @classmethod
    def convert_to_event(cls, proto_msg):
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
            logger.info("unknown radio message {}".format(type(proto_msg)))

    # sleep for a moment before sending data to the car so it doesn't collide with
    # data coming from the car as it passes the line
    def __delayed_send__(self, pos, delay):
        time.sleep(delay)
        self.radio.send_async(pos)


