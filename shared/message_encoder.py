
import time
import blowfish

from google.protobuf.message import Message
from shared.radio_message import ProtobufEnum


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
        msg.seq_num = self.seq
        msg.sender = self.sender
        msg.timestamp = int(time.time())
        payload = msg.SerializeToString()
        encrypted_payload = self.__do_encrypt(payload)
        # IDEA : if it's too long take out the sender and the timestamp?
        if len(encrypted_payload) > 240:
            raise MessageTooLongException()
        name = type(msg).__name__
        return b"LP" + bytes([ProtobufEnum[name].value]) + encrypted_payload

    def __do_encrypt(self, payload):
        if self.cipher:
            encrypted_payload = b"".join(self.cipher.encrypt_ecb_cts(payload))
            return encrypted_payload
        else:
            return payload
