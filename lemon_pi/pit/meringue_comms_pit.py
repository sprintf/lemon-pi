import logging
from threading import Thread
from time import sleep

import grpc

from lemon_pi.pit.event_defs import RadioReceiveEvent
from lemon_pi.pit.radio_interface import RadioInterface
from lemon_pi.shared.meringue_comms import MeringueComms, build_auth_header
from lemon_pi_pb2 import CarNumber, ToPitMessage

logger = logging.getLogger(__name__)


class MeringueCommsPitsReader(Thread, MeringueComms):

    def __init__(self, pit_identifier, car_numbers: [str], key: str):
        Thread.__init__(self)
        MeringueComms.__init__(self, pit_identifier, key)
        self.pit_identifier = pit_identifier
        self.car_numbers = car_numbers
        self.key = key
        self.stopped: bool = False

    def per_car_runner(self, car_num):
        logger.info(f"launching receiver thread for car {car_num}")
        cn = CarNumber()
        cn.car_number = car_num
        while not self.stopped:
            try:
                for wrapped_message in \
                        self.stub.receiveCarMessages(request=cn,
                                                     metadata=build_auth_header(self.track_id,
                                                                                self.pit_identifier,
                                                                                self.key)):
                    logger.info(f"received {wrapped_message}")
                    if isinstance(wrapped_message, ToPitMessage) and wrapped_message.HasField("to_pit"):
                        pit_msg = getattr(wrapped_message, wrapped_message.WhichOneof("to_pit"))
                        RadioInterface.convert_to_event(pit_msg)
                        if pit_msg.sender == car_num:
                            RadioReceiveEvent.emit(car=pit_msg.sender)
            except grpc.RpcError as error:
                if error.code() == grpc.StatusCode.UNAVAILABLE:
                    logger.info("meringue server not available, sleeping")
                    sleep(60)
                elif error.code() == grpc.StatusCode.UNKNOWN and error.details() == "Stream removed":
                    logger.info("reconnecting to meringue, connection reset")
                else:
                    logger.exception("unknown error")
                    sleep(10)

    def run(self):
        for car_num in self.car_numbers:
            Thread(target=self.per_car_runner, args=[car_num], daemon=True).start()

