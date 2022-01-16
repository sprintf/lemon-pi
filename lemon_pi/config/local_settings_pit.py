from lemon_pi.config.settings_pit import *

RADIO_KEY = "mykey"

# provide a race id to track realtime results
# empty means disabled
RACE_ID = ""

# the race cars we want to track
# [] means no tracking
# must be set in conjunction with a RACE_ID
# this needs to be the ID of the car in the eyes of the race data (not what you call your car)
TARGET_CARS = ["62"]

# current track location code
TRACK_CODE = "test1"

# connect string to meringue
# MERINGUE_GRPC_OVERRIDE_URL = "localhost:9090"
