from lemon_pi.pit.event_defs import (
    RaceStatusEvent,
    LapCompletedEvent,
    PittingEvent,
    PingEvent,
    TelemetryEvent,
    SendMessageEvent,
    SendTargetTimeEvent,
    SendFastLapResetEvent,
    LeavingPitEvent
)
from lemon_pi.shared.events import EventHandler
from lemon_pi.shared.meringue_comms import MeringueComms
from lemon_pi_pb2 import (
    EnteringPits,
    Ping,
    CarTelemetry,
    ToCarMessage, LeavingPits, RaceStatus, RacePosition
)
from race_flag_status_pb2 import RaceFlagStatus

from threading import Thread
import logging

logger = logging.getLogger(__name__)


class RadioInterface(EventHandler):

    def __init__(self, comms_server: MeringueComms):
        self.comms_server = comms_server
        SendMessageEvent.register_handler(self)
        SendTargetTimeEvent.register_handler(self)
        SendFastLapResetEvent.register_handler(self)

    def handle_event(self, event, **kwargs):
        if event == SendMessageEvent:
            self.send_driver_message(**kwargs)
            return

        if event == SendTargetTimeEvent:
            self.send_target_time(**kwargs)
            return

        if event == SendFastLapResetEvent:
            self.send_fast_lap_reset(**kwargs)
            return

    def send_driver_message(self, car="", msg=""):
        wrapper = ToCarMessage()
        wrapper.message.text = msg
        wrapper.message.car_number = car
        self.comms_server.send_message_to_car(wrapper)

    def send_target_time(self, car="", target_time=2.0):
        wrapper = ToCarMessage()
        wrapper.set_target.car_number = car
        wrapper.set_target.target_lap_time = target_time
        self.comms_server.send_message_to_car(wrapper)

    def send_fast_lap_reset(self, car=""):
        wrapper = ToCarMessage()
        wrapper.reset_fast_lap.car_number = car
        self.comms_server.send_message_to_car(wrapper)

    @classmethod
    def convert_to_event(cls, proto_msg):
        if type(proto_msg) == EnteringPits:
            PittingEvent.emit(car=proto_msg.sender)
            return

        if type(proto_msg) == LeavingPits:
            LeavingPitEvent.emit(car=proto_msg.sender)
            return

        if type(proto_msg) == CarTelemetry:
            TelemetryEvent.emit(car=proto_msg.sender,
                                ts=proto_msg.timestamp,
                                coolant_temp=proto_msg.coolant_temp,
                                lap_count=proto_msg.lap_count,
                                last_lap_time=proto_msg.last_lap_time,
                                fuel_percent=proto_msg.fuel_remaining_percent)
            return

        if type(proto_msg) == Ping:
            PingEvent.emit(car=proto_msg.sender, ts=proto_msg.timestamp)
            return

        if type(proto_msg) == RaceStatus:
            RaceStatusEvent.emit(flag=RaceFlagStatus.Name(proto_msg.flag_status))
            return

        if type(proto_msg) == RacePosition:
            LapCompletedEvent.emit(
                car=proto_msg.car_number,
                laps=proto_msg.lap_count,
                position=proto_msg.position,
                class_position=proto_msg.position_in_class,
                last_lap_time=proto_msg.last_lap_time,
                gap=proto_msg.car_ahead.gap_text,
            )
            return

        logger.info("unknown radio message {}".format(type(proto_msg)))
