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
    DriverMessageAddendumEvent,
    RaceFlagStatusEvent,
    LapInfoEvent,
    RadioReceiveEvent,
    RefuelEvent,
    ExitApplicationEvent
)
from lemon_pi.shared.events import EventHandler
from lemon_pi.shared.generated.messages_pb2 import (
    RaceStatus,
    DriverMessage,
    Ping,
    RacePosition,
    RaceFlagStatus,
    SetFuelLevel,
    ToPitMessage, RemoteReboot)

from python_settings import settings

import logging

from lemon_pi.shared.radio import Radio

logger = logging.getLogger(__name__)


# an adapter class that gets radio events and then sends them onto the radio.
# This is a thread, because it listens for messages coming in from the radio, and we do
# not want to use the radio control thread for processing the messages. We need the radio
# control thread to be back controlling the radio

class RadioInterface(Thread, EventHandler):

    def __init__(self, radio:Radio,
                 temp_provider:TemperatureProvider,
                 lap_provider:LapProvider,
                 fuel_provider:FuelProvider):
        Thread.__init__(self)
        self.radio = radio
        self.temp_provider = temp_provider
        self.lap_provider = lap_provider
        self.gps_provider = None
        self.fuel_provider = fuel_provider
        RadioSyncEvent.register_handler(self)
        LeaveTrackEvent.register_handler(self)

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
            msg.telemetry.last_lap_fuel_usage = self.fuel_provider.get_fuel_used_last_lap_ml()
            msg.telemetry.fuel_remaining_percent = self.fuel_provider.get_fuel_percent_remaining()
            # we send the event asynchronously, because the radio can take multiple seconds
            # to transmit, so there is no guarantee that this message will be sent exactly now
            self.radio.send_async(msg)
        if event == LeaveTrackEvent:
            msg = ToPitMessage()
            msg.pitting.timestamp = 1
            self.radio.send_async(msg)

    def run(self):
        while True:
            try:
                msg = self.radio.receive_queue.get()
                self.process_incoming(msg)
                self.radio.receive_queue.task_done()
            except Exception:
                logger.exception("got an exception in radio_interface")

    def process_incoming(self, msg):
        RadioReceiveEvent.emit()
        if type(msg) == RaceStatus:
            logger.info("got race status message...{}".format(msg))
            RaceFlagStatusEvent.emit(flag=RaceFlagStatus.Name(msg.flag_status))
            if msg.flag_status == RaceFlagStatus.RED:
                DriverMessageEvent.emit(text="Race Red Flagged", duration_secs=10)
            if msg.flag_status == RaceFlagStatus.BLACK:
                DriverMessageEvent.emit(text="Race Black Flagged", duration_secs=10)
            if msg.flag_status == RaceFlagStatus.YELLOW:
                DriverMessageEvent.emit(text="Course Yellow", duration_secs=10)
        elif type(msg) == DriverMessage:
            logger.info("got race driver message...{}".format(msg))
            # for a multi-car team we only want to show the message to the car it
            # was intended for
            if msg.car_number == settings.CAR_NUMBER:
                DriverMessageEvent.emit(text=msg.text, duration_secs=30)
        elif type(msg) == Ping:
            logger.info("got ping message...{}".format(msg))
        elif type(msg) == RacePosition:
            logger.info("got race position message...{}".format(msg))
            # is this about us directly?
            if msg.car_number == settings.CAR_NUMBER:
                position_text = self.format_position(msg)
                if msg.car_ahead.car_number:
                    text = "{}  ▲ #{} by {}".format(position_text, msg.car_ahead.car_number, msg.car_ahead.gap_text)
                    DriverMessageEvent.emit(text=text, duration_secs=120)
                else:
                    # we're in the lead, there's no-one ahead
                    text = "P1"
                    DriverMessageEvent.emit(text=text, duration_secs=120)
                LapInfoEvent.emit(lap_count=msg.lap_count, ts=msg.timestamp)
            else:
                # this might be the following car behind us ... it might also be for a different car in our team
                if msg.car_ahead and msg.car_ahead.car_number == settings.CAR_NUMBER:
                    text = " ▼ #{} by {}".format(msg.car_number, msg.car_ahead.gap_text)
                    DriverMessageAddendumEvent.emit(text=text)
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
        else:
            logger.info("got unexpected message : {}".format(type(msg)))

    def format_position(self, msg: RacePosition):
        if msg.position_in_class > 0 and msg.position_in_class != msg.position:
            return "P{} ({})".format(msg.position, msg.position_in_class)
        return "P{}".format(msg.position)






