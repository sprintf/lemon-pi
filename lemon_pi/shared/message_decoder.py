
import blowfish

from lemon_pi_pb2 import ToCarMessage, ToPitMessage

from google.protobuf.message import Message
from google.protobuf.message import DecodeError


class NoiseException(Exception):
    pass


class LPiNoiseException(Exception):
    pass


class MessageDecoder:

    def __init__(self, key:str):
        self.key = key
        self.cipher = blowfish.Cipher(key.encode("UTF-8")) if len(key) else None

    def decode(self, payload:[bytes], instance: Message) -> Message:
        if not payload[0:2] == b"LP":
            raise NoiseException()
        encrypted_payload = payload[len("LP"):]
        # what about exceptions from this
        try:
            payload = self.__do_decrypt(encrypted_payload)
            parse_len = instance.ParseFromString(payload)
            # when this happens the parser gave up early, we do see a stdout message
            # "RuntimeWarning: Unexpected end-group tag: Not all data was converted"
            if parse_len < len(payload):
                raise DecodeError()
            if isinstance(instance, ToCarMessage) and instance.HasField("to_car"):
                return getattr(instance, instance.WhichOneof("to_car"))
            if isinstance(instance, ToPitMessage) and instance.HasField("to_pit"):
                return getattr(instance, instance.WhichOneof("to_pit"))
            raise RuntimeWarning("decoding failed")
        except RuntimeWarning:
            # this also means the decryption failed
            raise LPiNoiseException()
        except ValueError:
            # this means the decryption failed
            raise LPiNoiseException()
        except DecodeError:
            # another protobuf error we may see
            raise LPiNoiseException()

    def __do_decrypt(self, encrypted_payload):
        if self.cipher:
            return (b"".join(self.cipher.decrypt_ecb_cts(encrypted_payload)))
        else:
            return encrypted_payload

