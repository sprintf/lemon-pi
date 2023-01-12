import subprocess
from threading import Thread

from lemon_pi.car.display_providers import (
    TemperatureProvider,
    LapProvider,
    FuelProvider
)
from lemon_pi.car.event_defs import (
    LeaveTrackEvent,
    RadioSyncEvent,
    DriverMessageEvent,
    RaceFlagStatusEvent,
    LapInfoEvent,
    RadioReceiveEvent,
    RefuelEvent,
    ExitApplicationEvent, RacePositionEvent, SetTargetTimeEvent, RacePersuerEvent, ResetFastLapEvent, EnterTrackEvent
)
from lemon_pi.shared.events import EventHandler
from lemon_pi.shared.meringue_comms import MeringueComms
from lemon_pi_pb2 import (
    RaceStatus,
    DriverMessage,
    Ping,
    RacePosition,
    SetFuelLevel,
    ToPitMessage, RemoteReboot, SetTargetTime, ResetFastLap)
from race_flag_status_pb2 import RaceFlagStatus

from python_settings import settings

import logging

logger = logging.getLogger(__name__)


# an adapter class that gets radio events and then sends them onto the radio.
# This is a thread, because it listens for messages coming in from the radio, and we do
# not want to use the radio control thread for processing the messages. We need the radio
# control thread to be back controlling the radio

class RadioInterface(EventHandler):

    def __init__(self,
                 comms_server: MeringueComms,
                 temp_provider:TemperatureProvider,
                 lap_provider:LapProvider,
                 fuel_provider:FuelProvider):
        self.comms_server = comms_server
        self.temp_provider = temp_provider
        self.lap_provider = lap_provider
        self.gps_provider = None
        self.fuel_provider = fuel_provider
        RadioSyncEvent.register_handler(self)
        LeaveTrackEvent.register_handler(self)
        EnterTrackEvent.register_handler(self)

    def register_lap_provider(self, lap_provider):
        self.lap_provider = lap_provider

    def register_gps_provider(self, gps):
        self.gps_provider = gps

    def handle_event(self, event, **kwargs):
        if event == RadioSyncEvent:
            msg = ToPitMessage()
            msg.telemetry.coolant_temp = self.temp_provider.get_temp_f()
            msg.telemetry.last_lap_time = self.lap_provider.get_last_lap_time()
            msg.telemetry.lap_count = self.lap_provider.get_lap_count()
            msg.telemetry.fuel_remaining_percent = self.fuel_provider.get_fuel_percent_remaining()
            self.comms_server.send_message_from_car(msg)
            return

        if event == LeaveTrackEvent:
            msg = ToPitMessage()
            # we have to set some field to let protobuf know the message type
            msg.pitting.timestamp = 1
            self.comms_server.send_message_from_car(msg)
            return

        if event == EnterTrackEvent:
            msg = ToPitMessage()
            # we have to set some field to let protobuf know the message type
            msg.entering.timestamp = 1
            self.comms_server.send_message_from_car(msg)
            return

    def process_incoming(self, msg):
        RadioReceiveEvent.emit()
        # todo : check hash of timestamp + seqNum + sender => if it's been handled then skip it
        if type(msg) == RaceStatus:
            logger.info("got race status message...{}".format(msg))
            RaceFlagStatusEvent.emit(flag=RaceFlagStatus.Name(msg.flag_status))
            if msg.flag_status == RaceFlagStatus.RED:
                DriverMessageEvent.emit(text="Race Red Flagged", duration_secs=10, audio=True)
            if msg.flag_status == RaceFlagStatus.BLACK:
                DriverMessageEvent.emit(text="Race Black Flagged", duration_secs=10, audio=True)
            if msg.flag_status == RaceFlagStatus.YELLOW:
                DriverMessageEvent.emit(text="Course Yellow", duration_secs=10, audio=True)
        elif type(msg) == DriverMessage:
            logger.info("got race driver message...{}".format(msg))
            # for a multi-car team we only want to show the message to the car it
            # was intended for
            if msg.car_number == settings.CAR_NUMBER:
                DriverMessageEvent.emit(text=msg.text, duration_secs=30, audio=True)
        elif type(msg) == Ping:
            logger.info("got ping message...{}".format(msg))
        elif type(msg) == RacePosition:
            logger.info("got race position message...{}".format(msg))
            # is this about us directly?
            if msg.car_number == settings.CAR_NUMBER:
                RacePositionEvent.emit(pos=msg.position,
                                       pos_in_class=msg.position_in_class,
                                       car_ahead=msg.car_ahead.car_number,
                                       gap=msg.car_ahead.gap_text,
                                       gap_to_front=msg.gap_to_front)
                LapInfoEvent.emit(lap_count=msg.lap_count, ts=msg.timestamp)
            else:
                # this might be the following car behind us ... it might also be for a different car in our team
                if msg.car_ahead and msg.car_ahead.car_number == settings.CAR_NUMBER:
                    RacePersuerEvent.emit(car_behind=msg.car_number, gap=msg.car_ahead.gap_text)
            # now that this message also contains the race flag status we can emit it
            # unlike the similar message above this does not mean that the status has changed
            # it's more for corrective purposes, so the display doesn't get stuck in a bad
            # state if a flag message is missed
            RaceFlagStatusEvent.emit(flag=RaceFlagStatus.Name(msg.flag_status))
        elif type(msg) == SetFuelLevel:
            logger.info("got fuel level adjustment...{}".format(msg))
            # for a multi-car team we only want to show the message to the car it
            # was intended for
            if msg.car_number != settings.CAR_NUMBER:
                logger.info("it's not for me, ignoring")
                return
            if msg.percent_full == 0:
                RefuelEvent.emit(percent_full=100)
            else:
                RefuelEvent.emit(percent_full=msg.percent_full)
        elif type(msg) == RemoteReboot:
            # for a multi-car team we only want to show the message to the car it
            # was intended for
            if msg.car_number != settings.CAR_NUMBER:
                logger.info("it's not for me, ignoring")
                return
            logger.info("got remote reboot going down".format(msg))
            ExitApplicationEvent.emit()
            logger.info("told system to shut down ... now rebooting lemon-pi")
            subprocess.run(['sudo', 'reboot', 'now'])
            logger.info("goodbye, cruel world...")
        elif type(msg) == SetTargetTime:
            if msg.car_number != settings.CAR_NUMBER:
                logger.info("it's not for me, ignoring")
                return
            logger.info(f"got a target time of {msg.target_lap_time}")
            SetTargetTimeEvent.emit(target=msg.target_lap_time)
        elif type(msg) == ResetFastLap:
            if msg.car_number != settings.CAR_NUMBER:
                logger.info("it's not for me, ignoring")
                return
            logger.info(f"got a reset fast lap message")
            ResetFastLapEvent.emit()
        else:
            logger.info("got unexpected message : {}".format(type(msg)))

    def format_position(self, msg: RacePosition):
        if msg.position_in_class > 0 and msg.position_in_class != msg.position:
            return "P{} ({})".format(msg.position, msg.position_in_class)
        return "P{}".format(msg.position)






