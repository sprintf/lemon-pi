import time

from lemon_pi_pb2 import ToCarMessage, ToPitMessage


class MessagePostmarker:

    instance = None

    def __init__(self, sender: str):
        self.seq = 0
        self.sender = sender

    @classmethod
    def get_instance(cls, sender: str):
        if MessagePostmarker.instance is None:
            MessagePostmarker.instance = MessagePostmarker(sender)
        assert(MessagePostmarker.instance.sender == sender)
        return MessagePostmarker.instance

    def stamp(self, msg):
        subfield = None
        if isinstance(msg, ToCarMessage):
            subfield = msg.WhichOneof("to_car")
        if isinstance(msg, ToPitMessage):
            subfield = msg.WhichOneof("to_pit")

        if subfield is None:
            raise Exception("no particular message type indicated")

        subfield_attr = getattr(msg, subfield)

        if getattr(subfield_attr, "seq_num") != 0:
            return
        self.seq += 1
        setattr(subfield_attr, "seq_num", self.seq)
        setattr(subfield_attr, "sender", self.sender)
        setattr(subfield_attr, "timestamp", int(time.time()))
