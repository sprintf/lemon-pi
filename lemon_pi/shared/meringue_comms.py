import base64
import logging
import urllib

import grpc
from google.protobuf.empty_pb2 import Empty

from lemon_pi.shared.message_postmarker import MessagePostmarker
from lemon_pi_pb2 import ToCarMessage, ToPitMessage
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
        self.postmarker = MessagePostmarker.get_instance(sender)

    def is_ready(self):
        return self.ready

    def set_track_id(self, track_id):
        self.track_id = track_id
        logger.info(f"track id set to {track_id}")

    def configure(self, override_url):
        logger.info("preparing configuration")
        if override_url:
            self.channel = grpc.insecure_channel(override_url)
            logger.info(f"override insecure gRPC channel configured to {override_url}")
        else:
            url = self._lookup_service_url()
            logger.info(f"connecting to secure gRPC channel at {url}")
            credentials = grpc.ssl_channel_credentials()
            self.channel = grpc.secure_channel(f"{url}:443", credentials)
            logger.info("secure channel established")

        self.stub = CommsServiceStub(self.channel)
        self.ready = self.track_id is not None
        logger.info("ready to talk to meringue")
        self.stub.PingPong(request=Empty())

    def send_message_to_car(self, msg:ToCarMessage):
        if not self.ready:
            logger.info("not ready to talk to meringue")
            return
        self.postmarker.stamp(msg)
        self.stub.sendMessageFromPits(request=msg,
                                      metadata=build_auth_header(self.track_id, self.sender, self.key))
        logger.info("sent message to car")

    def send_message_from_car(self, msg:ToPitMessage):
        if not self.ready:
            logger.info("not ready to talk to meringue")
            return
        self.postmarker.stamp(msg)
        self.stub.sendMessageFromCar(request=msg,
                                     metadata=build_auth_header(self.track_id, self.sender, self.key))
        logger.info("sent message to pit")

    # also Todo : allow override of this when running locally
    def _lookup_service_url(self):
        #
        r = urllib.request.Request("https://storage.googleapis.com/perplexus/public/service_endpoint.txt")
        try:
            logger.info("checking for meringue service ...")
            resp = urllib.request.urlopen(r)
            return resp.read().decode("utf-8").strip()
        except urllib.error.URLError as e:
            logger.info("no wifi, failed to lookup meringue service")

def build_auth_header(track_id:str, car_num: str, key:str):
    return [("authorization", f"Basic {create_auth_token(track_id, car_num, key)}")]

def create_auth_token(track_id:str, car_num: str, key:str):
    return base64.standard_b64encode(f"{track_id}/{car_num}:{key}".encode("utf-8")).decode('utf-8')



