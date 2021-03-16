
import time
import blowfish

from google.protobuf.message import Message
from lemon_pi.shared.generated.messages_pb2 import ToCarMessage, ToPitMessage


class MessageTooLongException(Exception):
    pass


class MessageEncoder:

    def __init__(self, sender:str, key:str):
        self.seq = 0
        self.sender = sender
        self.key = key
        self.cipher = blowfish.Cipher(key.encode("UTF-8")) if len(key) else None

    def encode(self, msg:Message) -> [bytes]:
        self.seq += 1
        subfield = None
        if isinstance(msg, ToCarMessage):
            subfield = msg.WhichOneof("to_car")
            pass
        if isinstance(msg, ToPitMessage):
            subfield = msg.WhichOneof("to_pit")
            pass

        subfield_attr = getattr(msg, subfield)
        setattr(subfield_attr, "seq_num", self.seq)
        setattr(subfield_attr, "sender", self.sender)
        setattr(subfield_attr, "timestamp", int(time.time()))

        payload = msg.SerializeToString()
        encrypted_payload = self.__do_encrypt(payload)
        # IDEA : if it's too long take out the sender and the timestamp?
        if len(encrypted_payload) > 240:
            raise MessageTooLongException()
        name = type(msg).__name__
        return b"LP" + encrypted_payload

    def __do_encrypt(self, payload):
        if self.cipher:
            encrypted_payload = b"".join(self.cipher.encrypt_ecb_cts(payload))
            return encrypted_payload
        else:
            return payload
