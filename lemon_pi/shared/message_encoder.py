
import blowfish

from google.protobuf.message import Message
from lemon_pi.shared.message_postmarker import MessagePostmarker

class MessageTooLongException(Exception):
    pass


class MessageEncoder:

    def __init__(self, sender:str, key:str):
        self.seq = 0
        self.sender = sender
        self.key = key
        self.cipher = blowfish.Cipher(key.encode("UTF-8")) if len(key) else None
        self.postmarker = MessagePostmarker.get_instance(sender)

    def encode(self, msg:Message) -> [bytes]:
        # stamp the message, in case this hasn't happened yet
        self.postmarker.stamp(msg)

        payload = msg.SerializeToString()
        encrypted_payload = self.__do_encrypt(payload)
        # IDEA : if it's too long take out the sender and the timestamp?
        if len(encrypted_payload) > 240:
            raise MessageTooLongException()
        return b"LP" + encrypted_payload

    def __do_encrypt(self, payload):
        if self.cipher:
            encrypted_payload = b"".join(self.cipher.encrypt_ecb_cts(payload))
            return encrypted_payload
        else:
            return payload
