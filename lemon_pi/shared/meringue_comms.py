import base64
import logging
import time
import urllib
from queue import Queue
from threading import Thread
from urllib.request import Request
from urllib.error import URLError

import grpc
from google.protobuf.empty_pb2 import Empty
from grpc._channel import _InactiveRpcError

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
        self.ready = False
        self.send_queue = Queue()
        self.send_thread = Thread(target=self.__send_outbound_messages__, daemon=True)
        self.postmarker = MessagePostmarker.get_instance(sender)

    def is_ready(self):
        return self.ready

    def set_track_id(self, track_id):
        self.track_id = track_id
        logger.info(f"track id set to {track_id}")

    def configure(self, override_url):
        logger.info("preparing configuration")
        if override_url:
            if override_url.endswith(".app"):
                credentials = grpc.ssl_channel_credentials()
                self.channel = grpc.secure_channel(f"{override_url}:443", credentials)
            else:
                self.channel = grpc.insecure_channel(override_url)
            logger.info(f"override gRPC channel configured to {override_url}")
        else:
            url = self._lookup_service_url()
            logger.info(f"connecting to secure gRPC channel at {url}")
            credentials = grpc.ssl_channel_credentials()
            self.channel = grpc.secure_channel(f"{url}:443", credentials)
            logger.info("secure channel established")

        stub = CommsServiceStub(self.channel)
        stub.PingPong(request=Empty())
        self.ready = self.track_id is not None
        self.send_thread.start()
        logger.info("ready to talk to meringue")

    def send_message_to_car(self, msg:ToCarMessage):
        if not self.ready:
            logger.info("not ready to talk to meringue")
            return
        self.postmarker.stamp(msg)
        self.send_queue.put(msg)
        logger.debug("queued message to car")

    def send_message_from_car(self, msg:ToPitMessage):
        if not self.ready:
            logger.info("not ready to talk to meringue")
            return
        self.postmarker.stamp(msg)
        self.send_queue.put(msg)
        logger.debug("queued message to pit")

    def __send_outbound_messages__(self):
        stub = CommsServiceStub(self.channel)
        logger.debug("sending outbound messages...")
        while True:
            try:
                logger.debug("awaiting message...")
                msg = self.send_queue.get()
                logger.debug("got a message to send!!")
                # if the message is more than 60 seconds old then discard it
                if time.time() - self.postmarker.get_timestamp(msg) > 60:
                    logger.info("discarding out of date message")
                    continue

                if isinstance(msg, ToCarMessage):
                    stub.sendMessageFromPits(request=msg, timeout=10,
                                             metadata=build_auth_header(self.track_id, self.sender, self.key))
                if isinstance(msg, ToPitMessage):
                    stub.sendMessageFromCar(request=msg, timeout=10,
                                            metadata=build_auth_header(self.track_id, self.sender, self.key))
                logger.debug("sent message")
            except _InactiveRpcError:
                logger.info("failed to send message")
            except Exception:
                logger.exception("surprise!")
            finally:
                self.send_queue.task_done()


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



