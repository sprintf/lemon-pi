
# DISPLAY_WIDTH = 1024
# DISPLAY_HEIGHT = 600
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

# enable for touchscreens, by default disabled
EXIT_BUTTON_ENABLED = False

# the size of the vehicle's fuel tank
FUEL_CAPACITY_US_GALLONS = 15

# the time taken to complete a radio command
RADIO_CMD_COMPLETION_TIME = 0.1

# make sure this is specified in your local config, it must be the
# same value in both your car and pit config
# RADIO_KEY = "abracadabra"

# make sure this is specified in your local config
# RADIO_DEVICE = CAR_NUMBER = "100"

# protocol for OBD
# see elm327.py for the list
OBD_PROTOCOL = "3"

# temperature bands : display colorizes in these bands
TEMP_BAND_LOW = 180
TEMP_BAND_WARN = 205
TEMP_BAND_HIGH = 215

# there's only room for 8 lines of text in here
ENTER_PIT_INSTRUCTIONS = """1. Loosen Belts
2. Undo Belts
3. Disc. Radio
4. Stop (no h-brake)
5. Wheel Off
6. Kill Switch
7. Get Out!
"""

# no more than 8 lines of text here either
SET_OFF_INSTRUCTIONS = """1. Adjust Seat
2. Wheel On
3. Belts
4. Radio
5. Mirrors
6. Water
Gloves? HANS?
"""