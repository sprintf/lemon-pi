
from enum import Enum
from lemon_pi.shared.generated.messages_pb2 import (
    Ping,
    DriverMessage,
    RaceStatus,
    RacePosition,
    CarTelemetry,
    EnteringPits)


class ProtobufEnum(Enum):
   Ping = 0
   DriverMessage = 1
   RaceStatus = 2
   RacePosition = 3
   CarTelemetry = 4
   EnteringPits = 5

class UnknownRadioMessage(Exception):
    pass


def create_instance(msg:ProtobufEnum):
    if msg == ProtobufEnum.Ping:
        return Ping()
    elif msg == ProtobufEnum.DriverMessage:
        return DriverMessage()
    elif msg == ProtobufEnum.RaceStatus:
        return RaceStatus()
    elif msg == ProtobufEnum.RacePosition:
        return RacePosition()
    elif msg == ProtobufEnum.CarTelemetry:
        return CarTelemetry()
    elif msg == ProtobufEnum.EnteringPits:
        return EnteringPits()
    raise UnknownRadioMessage()


