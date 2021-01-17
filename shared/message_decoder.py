
import base64
import blowfish
from io import StringIO
from shared.radio_message import (
    ProtobufEnum, create_instance
)

from google.protobuf.message import Message
from google.protobuf.message import DecodeError
from shared.generated.ping_pb2 import Ping

class NoiseException(Exception):
    pass


class LPiNoiseException(Exception):
    pass


class MessageDecoder:

    def __init__(self, key:str):
        self.key = key
        self.cipher = blowfish.Cipher(key.encode("UTF-8")) if len(key) else None

    def decode(self, payload:[bytes]) -> Message:
        if not payload[0:2] == b"LP":
            # todo : write test for this
            raise NoiseException()
        instance = create_instance(ProtobufEnum(int(payload[2])))
        base64_payload = payload[len("LPx"):]
        # what about exceptions from this
        try:
            payload = self.__do_decrypt(base64_payload)
            instance.ParseFromString(payload)
            return instance
        except ValueError:
            raise LPiNoiseException()
        except DecodeError:
            raise LPiNoiseException()

    def __do_decrypt(self, base64_payload):
        if self.cipher:
            encrypted_payload = base64_payload # base64.b64decode(base64_payload)
            return (b"".join(self.cipher.decrypt_ecb_cts(encrypted_payload)))
        else:
            return base64_payload

if __name__ == "__main__":
    raw = "radio_rx  4C50697879675965642B4B69585A645551393635532F58697A35696967613154617269783437624E6646304F6C3379662B764959465244357A39357056486D316A514248524A55385778652B7745512F7A43586F31733D"
    decoder = MessageDecoder("")
    raw = raw[10:]
    raw = bytes(bytearray.fromhex(raw))
    decoder.decode(raw)
