import base64
import logging
import time
import urllib

import grpc

from lemon_pi_pb2 import ToCarMessage, ToPitMessage, CarNumber
from lemon_pi_pb2_grpc import CommsServiceStub

logger = logging.getLogger(__name__)


class MeringueComms:

    # initialize this with a track code
    def __init__(self, sender:str, key:str):
        self.track_id = None
        self.sender = sender
        self.key = key
        self.seq = 0
        self.channel = None
        self.stub = None
        self.ready = False

    def set_track_id(self, track_id):
        self.track_id = track_id
        logger.info(f"track id set to {track_id}")

    def configure(self, override_url):
        logger.info("preparing configuration")
        if override_url:
            self.channel = grpc.insecure_channel(override_url)
            logger.info("override insecure channel configured")
        else:
            url = self._lookup_service_url()
            self.channel = grpc.secure_channel(url, grpc.ssl_channel_credentials())
            logger.info("secure channel established")

        self.stub = CommsServiceStub(self.channel)
        self.ready = self.track_id is not None
        logger.info("ready to talk to meringue")

    def send_message_to_car(self, msg:ToCarMessage):
        if not self.ready:
            logger.info("not ready to talk to meringue")
            return
        self.postmarkToCarMessage(msg)
        self.stub.sendMessageFromPits(request=msg,
                                      metadata=_build_auth_header(self.track_id, self.sender, self.key))
        logger.info("send message to car")

    def send_message_from_car(self, msg:ToPitMessage):
        if not self.ready:
            logger.info("not ready to talk to meringue")
            return
        self.postmarkToPitMessage(msg)
        self.stub.sendMessageFromCar(request=msg,
                                     metadata=_build_auth_header(self.track_id, self.sender, self.key))
        logger.info("sent message to pit")

    def receive_car_messages(self, car_number:str):
        cn = CarNumber()
        cn.car_number = car_number
        for car_message in self.stub.receiveCarMessages(request=cn,
                                                        metadata=_build_auth_header(self.track_id, "pit-999", "key")):
            # todo : call radio interface with them
            pass

    def receive_pit_messages(self):
        # todo : implement all this
        pass

    def postmarkToCarMessage(self, msg: ToCarMessage):
        # set the sender, the time, the sequence number
        subfield = msg.WhichOneof("to_car")
        subfield_attr = getattr(msg, subfield)
        self.set_subfields(subfield_attr)

    def postmarkToPitMessage(self, msg: ToPitMessage):
        # set the sender, the time, the sequence number
        subfield = msg.WhichOneof("to_pit")
        subfield_attr = getattr(msg, subfield)
        self.set_subfields(subfield_attr)

    def set_subfields(self, subfield_attr):
        if getattr(subfield_attr, "seq_num") is None:
            setattr(subfield_attr, "seq_num", self.seq)
        if getattr(subfield_attr, "sender") is None:
            setattr(subfield_attr, "sender", self.sender)
        if getattr(subfield_attr, "timestamp") is None:
            setattr(subfield_attr, "timestamp", int(time.time()))

    # todo : move this into shared, add general radio stuff to send and listen for messages
    # also Todo : allow override of this when running locally
    def _lookup_service_url(self):
        #
        r = urllib.request.Request("https://storage.googleapis.com/perplexus/public/service.txt")
        try:
            logger.info("checking for meringue service ...")
            resp = urllib.request.urlopen(r)
            return resp.read.decode("utf-8")
        except urllib.error.URLError as e:
            logger.info("no wifi, failed to lookup meringue service")

def _build_auth_header(track_id:str, car_num: str, key:str):
    return [("authorization", f"Basic {_create_auth_token(track_id, car_num, key)}")]

def _create_auth_token(track_id:str, car_num: str, key:str):
    return base64.standard_b64encode(f"{track_id}/{car_num}:{key}".encode("utf-8")).decode('utf-8')



