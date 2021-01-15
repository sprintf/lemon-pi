
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
        self.cipher = blowfish.Cipher(key.encode("UTF-8")) if len(key) else None

    def decode(self, payload:[bytes]) -> RadioMessageBase:
        if not payload[0:3] == b"LPi":
            # todo : write test for this
            raise NoiseException()
        base64_payload = payload[len("LPi"):]
        # what about exceptions from this
        try:
            payload = self.__do_decrypt(base64_payload)
            if not (payload[0] == '{' and payload[-1] == '}'):
                raise LPiNoiseException()
            json_text = json.load(StringIO(payload))
            return RadioMessageBase.from_json(json_text)
        except ValueError:
            raise LPiNoiseException()
        except UnknownRadioMessage:
            raise LPiNoiseException()

    def __do_decrypt(self, base64_payload):
        if self.cipher:
            encrypted_payload = base64.b64decode(base64_payload)
            return (b"".join(self.cipher.decrypt_ecb_cts(encrypted_payload))).decode("UTF-8")
        else:
            return base64.b64decode(base64_payload).decode("UTF-8")

if __name__ == "__main__":
    raw = "radio_rx  4C50697879675965642B4B69585A645551393635532F58697A35696967613154617269783437624E6646304F6C3379662B764959465244357A39357056486D316A514248524A55385778652B7745512F7A43586F31733D"
    decoder = MessageDecoder("")
    raw = raw[10:]
    raw = bytes(bytearray.fromhex(raw))
    decoder.decode(raw)
