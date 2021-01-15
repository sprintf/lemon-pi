
import base64
import blowfish
from io import StringIO

from shared.radio_message import *


class NoiseException(Exception):
    pass


class LPiNoiseException(Exception):
    pass


class MessageDecoder:

    def __init__(self, key:str):
        self.key = key
        self.cipher = blowfish.Cipher(key.encode("UTF-8"))

    def decode(self, payload:[bytes]) -> RadioMessageBase:
        if not payload[0:3] == b"LPi":
            # todo : write test for this
            raise NoiseException()
        base64_payload = payload[len("LPi"):]
        # what about exceptions from this
        try:
            encrypted_payload = base64.b64decode(base64_payload)
            payload = b"".join(self.cipher.decrypt_ecb_cts(encrypted_payload)).decode("UTF-8")
            if not (payload[0] == '{' and payload[-1] == '}'):
                raise LPiNoiseException()
            json_text = json.load(StringIO(payload))
            return RadioMessageBase.from_json(json_text)
        except ValueError:
            raise LPiNoiseException()
        except UnknownRadioMessage:
            raise LPiNoiseException()
