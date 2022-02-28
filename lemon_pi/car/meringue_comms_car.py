import logging
from threading import Thread
from time import sleep

import grpc

from lemon_pi.car.radio_interface import RadioInterface
from lemon_pi.shared.data_provider_interface import GpsProvider
from lemon_pi.shared.meringue_comms import MeringueComms, build_auth_header
from lemon_pi_pb2 import CarNumber, ToCarMessage, ToPitMessage

logger = logging.getLogger(__name__)


class MeringueCommsCar(Thread, MeringueComms):

    def __init__(self, car_number: str, key: str, ):
        Thread.__init__(self)
        MeringueComms.__init__(self, car_number, key)
        self.car_number = car_number
        self.key = key
        self.radio_interface = None
        self.stopped: bool = False
        self.gps_provider = None

    def set_radio_interface(self, radio_interface: RadioInterface):
        self.radio_interface = radio_interface

    def register_gps_provider(self, gps: GpsProvider):
        self.gps_provider = gps

    def pinger(self):
        while not self.stopped:
            try:
                msg = ToPitMessage()
                position = self.gps_provider.get_gps_position()
                if position:
                    msg.ping.gps.CopyFrom(position)
                self.send_message_from_car(msg)
            except grpc.RpcError:
                pass
            sleep(30)

    def run(self):
        Thread(target=self.pinger, daemon=True).start()
        cn = CarNumber()
        cn.car_number = self.car_number
        while not self.stopped:
            try:
                for wrapped_message in \
                        self.stub.receivePitMessages(request=cn,
                                                     metadata=build_auth_header(self.track_id,
                                                                                self.car_number,
                                                                                self.key)):
                    logger.debug(f"received {wrapped_message}")
                    if isinstance(wrapped_message, ToCarMessage) and wrapped_message.HasField("to_car"):
                        car_msg = getattr(wrapped_message, wrapped_message.WhichOneof("to_car"))
                        self.radio_interface.process_incoming(car_msg)
            except grpc.RpcError as error:
                if error.code() == grpc.StatusCode.UNAVAILABLE:
                    logger.info("meringue server not available, sleeping")
                    sleep(60)
                elif error.code() == grpc.StatusCode.UNKNOWN and error.details() == "Stream removed":
                    logger.info("reconnecting to meringue, connection reset")
                else:
                    logger.exception("unknown error")
                    sleep(10)
