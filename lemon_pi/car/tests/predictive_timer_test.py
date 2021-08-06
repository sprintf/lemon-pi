import bisect
import re
import statistics
import unittest
from csv import reader

# csv columns
from lemon_pi.car.predictor import LapTimePredictor
from lemon_pi.car.target import Target

TIME = 0
ABS_TIME = 1
LAP = 2
SECTOR = 3
PREDICTED = 4
PREDICTED_VS_BEST = 5
GPS_UPDATE = 6
GPS_DELAY = 7
LAT = 8
LONG = 9
ALT_M = 10
ALT_F = 11
SPEED = 12
HEADING = 13



class PredictiveTimerTest(unittest.TestCase):

    def test_read_big_file(self):
        sonoma = Target("sonoma", (38.161340,-122.454911), (38.161589,-122.454658), direction="NW")
        plt = LapTimePredictor(sonoma)

        known_lap_times = {}
        lap_times: [float] = []

        with open("resources/test/sonoma-10-laps.csv") as f:
            pre_reader = reader(f)
            self.skip_preamble(pre_reader)
            line_count = 0
            lap_summary = re.compile('# Lap (\\d+): (\\d{2}):(\\d{2}):(\\d{2}).(\\d{3})')
            for row in pre_reader:
                line_count += 1
                match = lap_summary.match(row[0])
                if match:
                    lap = match.group(1)
                    mins = int(match.group(3))
                    secs = int(match.group(4))
                    msec = int(match.group(5))
                    lap_time = mins * 60 + secs + msec / 1000
                    print(f"lap {lap} time = {mins}:{secs}.{msec}  {lap_time}")
                    known_lap_times[lap] = lap_time
            print(f"scanned {line_count} lines")

        total_error_percentage = 0

        with open("resources/test/sonoma-full.csv") as f:
            csv_reader = reader(f)
            self.skip_preamble(csv_reader)
            line_count = 0
            last_cross_time = 0
            worst_gates_counts = {}

            for row in csv_reader:
                if row[0].startswith('#'):
                    continue
                line_count += 1
                crossed, cross_time = plt.update_position(float(row[LAT]),
                                                          float(row[LONG]),
                                                          round(float(row[HEADING])),
                                                          float(row[ABS_TIME]))

                if line_count % 100 == 0:
                    if row[LAP] not in known_lap_times:
                        break
                    actual_lap_time = known_lap_times[row[LAP]]
                    est_lap_time = plt.predict_lap()
                    if est_lap_time is None:
                        print(f"{plt.state} {row[LAP]} None")
                    elif actual_lap_time < 300:
                        mins = int(est_lap_time / 60)
                        secs = int(est_lap_time % 60)
                        alt_time = float(row[PREDICTED])
                        alt_mins = int(alt_time / 60)
                        alt_secs = int(alt_time % 60)
                        error_percent = abs(actual_lap_time - est_lap_time) / actual_lap_time * 100
                        total_error_percentage += error_percent
                        print(f"{row[LAP]} {plt.gate_index} {actual_lap_time} {error_percent:02.2f} {mins:02d}:{secs:02d} compared to {alt_mins:02d}:{alt_secs:02d}")

                if crossed:
                    lap_time = cross_time - last_cross_time
                    print(f"crossed line, lap_time = {lap_time}")
                    if lap_time <= 210:
                        ranking = bisect.bisect_left(lap_times, lap_time)
                        print(f"lapped ranked in position {ranking}")
                        bisect.insort(lap_times, lap_time)
                        gate_recent_ranks = self.extract_gate_recent_ranks(plt)
                        worst_gate = self.get_worst_gate_position(gate_recent_ranks, ranking)
                        print(f"gate recent ranks {gate_recent_ranks}")
                        print(f"worst gate is {worst_gate}")
                        existing_gate_worst_count = worst_gates_counts[worst_gate] if worst_gate in worst_gates_counts else 0
                        worst_gates_counts[worst_gate] = existing_gate_worst_count + 1
                    last_cross_time = cross_time

            print(f"best possible lap = {self.calculate_best_possible_lap(plt)}")
            #print(f"fifth best possible lap = {self.calculate_best_possible_lap(plt, index=4)}")
            print(f"total error percentage = {total_error_percentage:.0f}")
            # self.dump_top_gaps_whole_spans(plt)
            # print(f"gate 34 times_from_prev : {plt.gates[34].times_from_prev}")
            # print(f"gate 34 times_from_start : {plt.gates[34].times_from_start}")
            # print(f"worst gate counts = {worst_gates_counts}")


    @staticmethod
    def skip_preamble(csv_file):
        for row in csv_file:
            if len(row) == 0:
                continue
            if row[0].startswith('#'):
                continue
            break

    def extract_gate_recent_ranks(self, plt):
        result = []
        for g in plt.gates:
            result.append(g.last_mini_rank)
        return result

    def calculate_best_possible_lap(self, plt, index=0):
        result = 0
        time_to_finish = 0
        for g in plt.gates:
            print(f"debug: {g.target.name} {len(g.times_from_prev)} {len(g.times_from_start)}")
            seg_time = g.times_from_prev[index] if len(g.times_from_prev) > index else g.times_from_start[index]
            print(f"seg time = {seg_time}")
            result += seg_time
            time_to_finish = g.times_to_finish[index]
        print(f"time_to_finish = {time_to_finish}")
        return result + time_to_finish

    def dump_top_gaps_whole_spans(self, plt):
        for g in plt.gates:
            if len(g.times_from_prev):
                print(f"gate {g.target.name}")
                print(f"gap from best to second {g.times_from_prev[1] - g.times_from_prev[0]}")
                print(f"gap from best to 10th {g.times_from_prev[9] - g.times_from_prev[0]}")
                print(f"gap from best to worst {g.times_from_prev[-1] - g.times_from_prev[0]}")
                print(f"stddev of top 10 {statistics.stdev(g.times_from_prev[0:10])}")
                print("\n\n")

    @staticmethod
    def get_worst_gate_position(gate_recent_ranks, lap_rank):
        worst_position = -1
        worst_difference = 0
        for index, gate_rank in enumerate(gate_recent_ranks):
            if index < 4:
                continue
            diff = abs(gate_rank - lap_rank)
            if diff > worst_difference:
                worst_position = index
                worst_difference = diff
        return worst_position

# results
#
#  total error = 32872 with lookback 6 elements 20
#  total error = 32884 with lookback 5 elements 20
#  total error = 32961 with lookback 4 elements 20
#  back to 5  elements = 30
#   total error = 33352  lookback 5 element 30
#   total error = 33304  lookback 5 element 15
#   total error = 32853  lookback 5 element 18
#   total error = 33035  lookback 5 element 22
#   total error = 32736  lookback 5 element 200
#   total error = 32569  lookback 5 element 100
#   total error = 33362  lookback 5 element 50
#  when working recent split pos, skip missed gates from calc
#   total error = 33351  lookback 5 element 50
#   total error = 32563  lookback 5 element 100
#
#  bug fixes 32515  (throw out > 30% improvements in mini-splits)
#
#   changed to 1/6th of lap before predictions start
#   changed to be mean of recent and absolute
#   total error = 29389  lookback 5 element 100
#   total error = 30565  lookback 5 element 40
#   total error = 30075  lookback 5 element 20
#   total error = 30119  lookback 4 element 20
#   total error = 30061  lookback 6 element 20
#
#   bring in mean of this prediction and previous
#
#   ignore laps that are more than 5 mins... they accounted for 2/3 of error
#   total error = 10529  lookback 6 element 20
#
#    without smoothing from previous
#   total error = 10310  lookback 6 element 20
#   total error = 10325  lookback 5 element 20
#   total error = 10865  lookback 5 element 30
#   total error = 10270  lookback 5 element 18    <<< best so far
#   total error = 11177  lookback 5 element 12

# tuned throwout time at 35% rather than 25%

#   total error = 10259  lookback 5 element 18








