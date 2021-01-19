from threading import Thread

from car.display_providers import TemperatureProvider, LapProvider, FuelProvider
from car.events import EventHandler, CompleteLapEvent, LeaveTrackEvent, RadioSyncEvent
from shared.generated.messages_pb2 import (
    CarTelemetry,
    RaceStatus,
    DriverMessage,
    Ping,
    RacePosition,
    EnteringPits)

import logging

from shared.radio import Radio

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
        self.fuel_provider = fuel_provider
        CompleteLapEvent.register_handler(self)
        RadioSyncEvent.register_handler(self)
        LeaveTrackEvent.register_handler(self)

    def register_lap_provider(self, lap_provider):
        self.lap_provider = lap_provider

    def handle_event(self, event, **kwargs):
        if event == CompleteLapEvent or event == RadioSyncEvent:
            telemetry = CarTelemetry()
            telemetry.coolant_temp = self.temp_provider.get_temp_f()
            telemetry.last_lap_time = self.lap_provider.get_last_lap_time()
            telemetry.lap_count = self.lap_provider.get_lap_count()
            telemetry.last_lap_fuel_usage = self.fuel_provider.get_fuel_used_last_lap_ml()
            telemetry.fuel_remaining_percent = self.fuel_provider.get_fuel_percent_remaining()
            # we send the event asynchronously, because the radio can take multiple seconds
            # to transmit, so there is no guarantee that this message will be sent exactly now
            self.radio.send_async(telemetry)
        if event == LeaveTrackEvent:
            self.radio.send_async(EnteringPits())

    def run(self):
        msg = self.radio.receive_queue.get()
        if msg:
            self.process_incoming(msg)
            self.radio.receive_queue.task_done()

    def process_incoming(self, msg):
        if type(msg) == RaceStatus:
            logger.info("got race status message...{}".format(msg))
        elif type(msg) == DriverMessage:
            logger.info("got race driver message...{}".format(msg))
        elif type(msg) == Ping:
            logger.info("got ping message...{}".format(msg))
        elif type(msg) == RacePosition:
            logger.info("got race position message...{}".format(msg))
        else:
            logger.warning("got unexpected message : {}".format(type(msg)))




