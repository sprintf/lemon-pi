from pit.events import RaceStatusEvent, LapCompletedEvent
from pit.leaderboard import RaceOrder, CarPosition


class DataSourceHandler:

    def __init__(self, leaderboard:RaceOrder, target_car):
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
                        self.leaderboard.add_car(CarPosition(bits[1].strip('"'), bits[4].strip('"') + bits[5].strip('"')))
                    if bits[0] == "$F" and len(bits) == 6:
                        # print(bits)
                        if self.race_flag != bits[5].strip('" '):
                            self.race_flag = bits[5].strip('" ')
                            RaceStatusEvent.emit(flag=self.race_flag)
                    if bits[0] == "$G" and len(bits) == 5:
                        # print(bits)
                        car_number = bits[2].strip('"')
                        self.leaderboard.update_position(car_number, int(bits[1]))
                        if bits[3].isnumeric():
                            self.leaderboard.update_lap_count(car_number, int(bits[3]))
                    if bits[0] == "$H" and len(bits) == 5:
                        # print(bits)
                        car_number = bits[2].strip('"')
                        self.leaderboard.update_fastest_lap(car_number, int(bits[3]), bits[4].strip('"'))
                    if bits[0] == "$J" and len(bits) == 4:
                        # print(bits)
                        car_number = bits[1].strip('"')
                        self.leaderboard.update_last_lap(car_number, bits[2].strip('"'))
                    if bits[0] == "$RMLT" and len(bits) == 3:
                        # print(bits)
                        car_number = bits[1].strip('"')
                        self.leaderboard.update_lap_timestamp(car_number, int(bits[2]))
                    if bits[0] == "$RMHL" and len(bits) == 7:
                        car_number = bits[1].strip('"')
                        laps = int(bits[2].strip('"'))
                        position = int(bits[3].strip('"'))
                        last_lap = bits[4]
                        if car_number == self.target_car:
                            target = self.leaderboard.number_lookup.get(self.target_car)
                            ahead = target.car_in_front
                            gap = target.gap()
                            self.emit_lap_completed(car_number, laps, position, ahead, gap)
                        else:
                            this_car = self.leaderboard.number_lookup.get(car_number)
                            if not this_car:
                                return
                            ahead = this_car.car_in_front
                            if ahead and ahead.car_number == self.target_car:
                                gap = this_car.gap()
                                self.emit_lap_completed(car_number, laps, position, ahead, gap)
        except Exception as e:
            print(e)

    def emit_lap_completed(self, car_number, laps, position, ahead, gap):
        if ahead:
            LapCompletedEvent.emit(car=car_number, laps=laps, position=position, ahead=ahead.car_number, gap=gap)
        else:
            LapCompletedEvent.emit(car=car_number, laps=laps, position=position, ahead=None, gap="-")
