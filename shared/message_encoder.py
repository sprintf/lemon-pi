
import time
import base64
import blowfish

from shared.radio_message import RadioMessageBase

class MessageTooLongException(Exception):
    pass

class MessageEncoder:

    def __init__(self, sender:str, key:str):
        self.seq = 0
        self.sender = sender
        self.key = key
        self.cipher = blowfish.Cipher(key.encode("UTF-8"))

    def encode(self, msg:RadioMessageBase) -> [bytes]:
        self.seq += 1
        msg.seq = self.seq
        msg.sender = self.sender
        msg.ts = int(time.time())
        payload = msg.to_json()
        encrypted_payload = b"".join(self.cipher.encrypt_ecb_cts(payload.encode("UTF-8")))
        base64_payload = base64.b64encode(encrypted_payload)
        # IDEA : if it's too long take out the sender and the timestamp?
        if len(base64_payload) > 240:
            raise MessageTooLongException()
        return b"LPi" + base64_payload
