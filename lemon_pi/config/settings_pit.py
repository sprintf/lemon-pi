

# the number of seconds to delay sending race data to the car
# we can't send it as ther car hits the line because the car is sending us stuff
RACE_DATA_SEND_DELAY_SEC=3

# the time taken to complete a radio command
RADIO_CMD_COMPLETION_TIME = 0.1

# make sure this is specified in your local config, it must be the
# same value in both your car and pit config
# RADIO_KEY = "abracadabra"

# set this to the team name or your car number in the car
# it identifies the sender within this radio group
RADIO_DEVICE = "pit"

# temperature bands : display colorizes in these bands
TEMP_BAND_LOW = 180
TEMP_BAND_WARN = 205
TEMP_BAND_HIGH = 215

# current track location code
TRACK_CODE = "test1"

