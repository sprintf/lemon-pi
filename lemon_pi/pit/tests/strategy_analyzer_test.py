

import unittest
from unittest.mock import patch

from lemon_pi.pit.event_defs import LapCompletedEvent
from lemon_pi.pit.leaderboard import CarPosition, RaceOrder
from lemon_pi.pit.strategy_analyzer import StrategyAnalyzer


class StrategyAnalyzerTestCase(unittest.TestCase):

    @patch("lemon_pi.pit.event_defs.TargetTimeEvent.emit")
    def test_nothing_ahead(self, event):
        race = RaceOrder()
        race.add_car(CarPosition("181", "Perplexus Racing"))
        sa = StrategyAnalyzer(race, "181")
        race.update_last_lap("181", 109.608)
        sa.handle_event(LapCompletedEvent,
                        car="181", laps=10, position=1, last_lap_time=109.608)
        self.assertAlmostEqual(109.6, sa.get_target_time(), 1)
        event.assert_called()

    @patch("lemon_pi.pit.event_defs.TargetTimeEvent.emit")
    def test_one_car_ahead(self, event):
        race = RaceOrder()
        race.add_car(CarPosition("181", "Perplexus Racing"))
        race.add_car(CarPosition("182", "Second Place"))
        sa = StrategyAnalyzer(race, "182")
        race.update_last_lap("181", 109.608)
        sa.handle_event(LapCompletedEvent,
                        car="181", laps=10, position=1, last_lap_time=109.608)
        race.update_last_lap("182", 112.1)
        sa.handle_event(LapCompletedEvent,
                        car="182", laps=10, position=2, last_lap_time=112.1)
        self.assertAlmostEqual(108.6, sa.get_target_time(), 1)
        event.assert_called()

    @patch("lemon_pi.pit.event_defs.TargetTimeEvent.emit")
    def test_many_cars_ahead(self, event):
        race = RaceOrder()
        for car in range(100, 110):
            race.add_car(CarPosition(str(car), str(car)))
        race.add_car(CarPosition("181", "Perplexus Racing"))

        sa = StrategyAnalyzer(race, "181")

        for car in range(100, 110):
            lap_time = 60.836 + (car % 10)
            race.update_last_lap(str(car), lap_time)
            sa.handle_event(LapCompletedEvent,
                            car=str(car), laps=10, position=car - 99, last_lap_time=lap_time)
        race.update_last_lap("181", 105.999)
        sa.handle_event(LapCompletedEvent,
                        car="181", laps=10, position=11, last_lap_time=105.999)
        self.assertAlmostEqual(65.3, sa.get_target_time(), 1)
        event.assert_called()
