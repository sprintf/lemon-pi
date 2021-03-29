from lemon_pi.pit.event_defs import RaceStatusEvent, LapCompletedEvent
from lemon_pi.pit.leaderboard import RaceOrder, CarPosition
from datetime import datetime


class DataSourceHandler:

    def __init__(self, leaderboard: RaceOrder, target_car):
        self.leaderboard = leaderboard
        self.race_flag = ""
        self.target_car = target_car

    def handle_message(self, raw_line):
        try:
            line = raw_line.strip()
            if len(line) > 0:
                bits = line.split(",")
                if len(bits) > 0:
                    if bits[0] == "$COMP":
                        self.leaderboard.add_car(CarPosition(bits[1].strip('"'),
                                                             bits[4].strip('"') + bits[5].strip('"'),
                                                             class_id=int(bits[3])))
                    if bits[0] == "$C":
                        self.leaderboard.add_class(int(bits[1]), bits[2].strip('"'))
                    if bits[0] == "$F" and len(bits) == 6:
                        # print(bits)
                        if self.race_flag != bits[5].strip('" '):
                            self.race_flag = bits[5].strip('" ')
                            RaceStatusEvent.emit(flag=self.race_flag)
                    if bits[0] == "$G" and len(bits) == 5:
                        # "$G" indicates a cars position and number of laps completed
                        # print(bits)
                        # $G,14,"128",24,"00:59:45.851"
                        car_number = bits[2].strip('"')
                        laps_completed = None
                        if bits[3].isnumeric():
                            laps_completed = int(bits[3])
                        self.leaderboard.update_position(car_number, int(bits[1]), laps_completed)
                    if bits[0] == "$H" and len(bits) == 5:
                        # print(bits)
                        car_number = bits[2].strip('"')
                        self.leaderboard.update_fastest_lap(car_number,
                                                            int(bits[3]),
                                                            self._convert_to_s(bits[4].strip('"')))
                    if bits[0] == "$J" and len(bits) == 4:
                        # print(bits)
                        car_number = bits[1].strip('"')
                        self.leaderboard.update_last_lap(car_number, self._convert_to_s(bits[2].strip('"')))
                    if bits[0] == "$RMLT" and len(bits) == 3:
                        # print(bits)
                        car_number = bits[1].strip('"')
                        self.leaderboard.update_lap_timestamp(car_number, int(bits[2]))
                    if bits[0] == "$RMHL" and len(bits) == 7:
                        car_number = bits[1].strip('"')
                        laps = int(bits[2].strip('"'))
                        position = int(bits[3].strip('"'))
                        last_lap_time = self._convert_to_s(bits[4].strip('"'))
                        flag = bits[5].strip('" ')
                        self.leaderboard.update_position(car_number, position, laps)
                        if car_number == self.target_car:
                            target = self.leaderboard.number_lookup.get(self.target_car)
                            ahead = target.car_in_front
                            gap = target.gap(ahead)
                            self.emit_lap_completed(car_number, laps, position,
                                                    target.class_position, ahead,
                                                    gap, last_lap_time, flag)
                        else:
                            this_car = self.leaderboard.number_lookup.get(car_number)
                            if not this_car:
                                return
                            ahead = this_car.car_in_front
                            if ahead and ahead.car_number == self.target_car:
                                gap = this_car.gap(ahead)
                                self.emit_lap_completed(car_number, laps, position,
                                                        this_car.class_position, ahead,
                                                        gap, last_lap_time, flag)
        except Exception as e:
            print(e)

    @classmethod
    def emit_lap_completed(cls, car_number, laps, position, class_position, ahead, gap, last_lap_time, flag):
        if ahead:
            LapCompletedEvent.emit(car=car_number,
                                   laps=laps,
                                   position=position,
                                   class_position=class_position,
                                   ahead=ahead.car_number,
                                   gap=gap,
                                   last_lap_time=last_lap_time,
                                   flag=flag)
        else:
            LapCompletedEvent.emit(car=car_number,
                                   laps=laps,
                                   position=position,
                                   ahead=None,
                                   gap="-",
                                   last_lap_time=last_lap_time,
                                   flag=flag)

    @classmethod
    def _convert_to_s(cls, string_time) -> float:
        if "." in string_time:
            format_string = "%H:%M:%S.%f"
        else:
            format_string = "%H:%M:%S"
        date_time = datetime.strptime(string_time, format_string)
        td = date_time - datetime(1900, 1, 1)
        return td.total_seconds()
