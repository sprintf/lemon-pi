from pit.events import EventHandler, RaceStatusEvent, LapCompletedEvent
from shared.generated.messages_pb2 import RaceStatus, RacePosition, Opponent
from shared.radio import Radio


class RadioInterface(EventHandler):

    def __init__(self, radio:Radio):
        self.radio = radio

    def handle_event(self, event, **kwargs):
        if event == RaceStatusEvent:
            self.send_race_status(**kwargs)

        if event == LapCompletedEvent:
            self.send_lap_completed(**kwargs)

    def send_race_status(self, flag=""):
        status = RaceStatus()
        status.flagStatus = RaceStatus.RaceFlagStatus.UNKNOWN
        try:
            # this can fail with an empty string, in which case it remains
            # set to UNKNOWN
            status.flagStatus = RaceStatus.RaceFlagStatus.Value(flag.upper())
        except ValueError:
            pass
        self.radio.send_async(status)

    def send_lap_completed(self, car="", position=0, laps=0, ahead=None, gap="" ):
        pos = RacePosition()
        pos.car_number = car
        pos.position = position
        pos.lap_count = laps
        if ahead:
            pos.car_ahead.car_number = ahead
            pos.car_ahead.gap_text = gap
        self.radio.send_async(pos)