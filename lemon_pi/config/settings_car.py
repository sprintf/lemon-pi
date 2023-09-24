
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 576

# enable for touchscreens, by default disabled
EXIT_BUTTON_ENABLED = False

# the size of the vehicle's fuel tank
FUEL_CAPACITY_US_GALLONS = 15

# fuel fiddle percentage : in range -100 to +100
# if you are using 10% more fuel than expected then set this to 10
# if you are using 10% less fuel than expected then set this to -10
FUEL_FIDDLE_PERCENT = 0

# the frequency the car should ping it's position to the server.
# set to 30 for very occasional pings
# set to 1 for constant updates. There's no point going more than the GPS can provide
CAR_PING_FREQUENCY = 5

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
OBD_FAST = True

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

# should gps be logged?
LOG_GPS = False

# set gpsctl arguments to something specific
# for some GPS chips force nmea with "-n"
# for faster cycle time do "-c 0.5"
# for both try "-n -c 0.5"
GPSCTL_ARGS = ""

# distance between virtual gates on the track
VGATE_SEPARATION_FEET = 200


# You can set these in here, but you must manually run
#  sudo PYTHONPATH=. ./venv/bin/python3 lemon_pi/car/wifi.py
# This command will update the local settings, then reboot to connect
WIFI_SSID = None
WIFI_PASSWORD = None

# don't make audio announcements (mac-only disablement)
AUDIO_DISABLED = False
# don't annouce the gap to the front
AUDIO_ANNOUNCE_GAP_TO_FRONT = False


