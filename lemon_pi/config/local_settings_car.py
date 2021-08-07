from lemon_pi.config.settings_car import *

# the size of the vehicle's fuel tank
FUEL_CAPACITY_US_GALLONS = 17.5

# set this encryption key to the same value in the car(s)
# and the pit
RADIO_KEY = "mykey"

# your car number is used for identifying your radio device
# as well as working out which messages are for this car
RADIO_DEVICE = CAR_NUMBER = "181"


# optionally disable OBD
OBD_DISABLED = True

# optionally disable Radio
RADIO_DISABLED = False

# optionally disable GPS
GPS_DISABLED = False

LOG_GPS = False
GPS_CYCLE = "0.5"
VGATE_SEPARATION_FEET = 100

