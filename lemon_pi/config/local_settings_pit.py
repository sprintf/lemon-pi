from lemon_pi.config.settings_pit import *

RADIO_KEY = "mykey"

# provide a race id to track realtime results
# empty means disabled
RACE_ID = "37872"

# the race cars we want to track
# [] means no tracking
# must be set in conjunction with a RACE_ID
# this needs to be the ID of the car in the eyes of the race data (not what you call your car)
TARGET_CARS = ["23", "62"]
