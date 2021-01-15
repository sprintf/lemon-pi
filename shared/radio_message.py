
import json
from enum import Enum

class UnknownRadioMessage(Exception):
    pass


def create_instance(cmd:str):
    if cmd == 'ping':
        return PingMessage()
    elif cmd == "DM":
        return DriverMessage('')
    elif cmd == 'status':
        return RaceStatusMessage(RaceStatus.UNKNOWN)
    raise UnknownRadioMessage()


class RadioMessageBase:

    def __init__(self, cmd:str):
        self.cmd = cmd
        self.sender = ""
        self.ts = 0
        self.seq = 0

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    def from_json(data):
        result = create_instance(data['cmd'])
        for key, value in data.items():
            setattr(result, key, value)
        return result

    def __repr__(self):
        return self.to_json()


class PingMessage(RadioMessageBase):

    def __init__(self):
        RadioMessageBase.__init__(self, "ping")


class DriverMessage(RadioMessageBase):

    def __init__(self, driver_message):
        RadioMessageBase.__init__(self, "DM")
        self.dm = driver_message


class RaceStatus(str, Enum):
    UNKNOWN = ''
    GREEN = 'green'
    YELLOW = 'yellow'
    RED = 'red'
    BLACK = 'black'


class RaceStatusMessage(RadioMessageBase):

    def __init__(self, status:RaceStatus):
        RadioMessageBase.__init__(self, "status")
        self.status = status

