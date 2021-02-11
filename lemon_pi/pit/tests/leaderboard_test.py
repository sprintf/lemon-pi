import unittest

from lemon_pi.pit.leaderboard import CarPosition, RaceOrder


class LeaderboardTestCase(unittest.TestCase):

    def test_empty_is_ok(self):
        race = RaceOrder()
        self.assertTrue(race.__check_data_structure__())

    def test_race_with_one_car(self):
        race = RaceOrder()
        race.add_car(CarPosition("181", "Perplexus Racing"))
        self.assertTrue(race.__check_data_structure__())
        self.assertEqual(1, race.size())
        # start the race
        race.update_position("181", 1)
        self.assertTrue(race.__check_data_structure__())

    def test_race_with_two_cars(self):
        race = RaceOrder()
        race.add_car(CarPosition("181", "Perplexus Racing"))
        race.add_car(CarPosition("180", "Black BMW"))
        self.assertTrue(race.__check_data_structure__())
        self.assertEqual(2, race.size())
        # start the race
        race.update_position("181", 1)
        self.assertTrue(race.__check_data_structure__())

    def test_two_cars_other_order(self):
        race = RaceOrder()
        race.add_car(CarPosition("180", "Black BMW"))
        race.add_car(CarPosition("181", "Perplexus Racing"))
        self.assertTrue(race.__check_data_structure__())
        self.assertEqual(2, race.size())
        # start the race
        race.update_position("181", 1)
        self.assertTrue(race.__check_data_structure__())
        self.assertPositions(race, ["181", "180"])

    def test_race_with_multiple_cars(self):
        race = RaceOrder()
        race.add_car(CarPosition("181", "Perplexus Racing"))
        race.add_car(CarPosition("183", "Mazda GTX"))
        race.add_car(CarPosition("180", "Black BMW"))
        self.assertTrue(race.__check_data_structure__())
        self.assertEqual(3, race.size())
        # start the race
        race.update_position("181", 1)
        self.assertTrue(race.__check_data_structure__())
        race.update_position("180", 2)
        self.assertTrue(race.__check_data_structure__())
        race.update_position("183", 3)
        self.assertTrue(race.__check_data_structure__())
        self.assertPositions(race, ["181", "180", "183"])

    def test_preplexus_last_to_first(self):
        race = RaceOrder()
        race.add_car(CarPosition("181", "Perplexus Racing"))
        race.add_car(CarPosition("183", "Mazda GTX"))
        race.add_car(CarPosition("180", "Black BMW"))
        race.add_car(CarPosition("2", "Cervesa"))
        race.add_car(CarPosition("999", "Non-starter"))

        race.update_position("2", 1)
        race.update_position("180", 2)
        race.update_position("183", 3)
        race.update_position("181", 4)

        self.assertTrue(race.__check_data_structure__())

        # lap 2 happens and there a big overtake
        race.update_position("181", 1)
        race.update_position("2", 2)
        race.update_position("180", 3)
        race.update_position("183", 4)
        self.assertTrue(race.__check_data_structure__())
        self.assertPositions(race, ["181", "2", "180", "183"])

    def test_out_of_order_initialization(self):
        race = RaceOrder()
        race.add_car(CarPosition("181", "Perplexus Racing"))
        race.add_car(CarPosition("183", "Mazda GTX"))
        race.add_car(CarPosition("180", "Black BMW"))
        race.add_car(CarPosition("2", "Cervesa"))
        race.add_car(CarPosition("999", "Non-starter"))

        # when race data arrives as we join partway through a race the
        # entries come in out of sequential order
        race.update_position("180", 3)
        race.update_position("2", 4)
        race.update_position("183", 2)
        race.update_position("181", 1)

        self.assertTrue(race.__check_data_structure__())
        self.assertPositions(race, ["181", "183", "180", "2"])


    def assertPositions(self, race, expected_order:list):
        for pos, car in enumerate(expected_order):
            self.assertEqual(pos + 1, race.number_lookup.get(car).position)


# try same car twice
# try not updating to 1 in first position update
# try same number twice : different car
# try negative laps


if __name__ == '__main__':
    unittest.main()
