# a simple event framework so we can connect together decoupled logic
from lemon_pi.shared.events import Event

# the car is moving
MovingEvent = Event("Moving", suppress_logs=True, debounce_time=1)

# the car is not moving
NotMovingEvent = Event("NotMoving", suppress_logs=True, debounce_time=1)

# the car is exiting the race track and entering the pits
LeaveTrackEvent = Event("LeaveTrack", debounce_time=30)

# the car is entering the race track
EnterTrackEvent = Event("EnterTrack", debounce_time=30)

# a lap has been completed
# lap_count=   int
# lap_time=  float
CompleteLapEvent = Event("CompleteLap")

# a request to exit the application
ExitApplicationEvent = Event("ExitApplication")

# the car should transmit status on radio
RadioSyncEvent = Event("RadioSync", debounce_time=30)

### State Change Events

# the car is setting off from pits
StateChangeSettingOffEvent = Event("StateChangeSettingOff", debounce_time=10)

# the car is parked in the pits
StateChangePittedEvent = Event("StateChangePitted")

### OBD Events
OBDConnectedEvent = Event("OBD-Connected")
OBDDisconnectedEvent = Event("OBD-Disconnected")

### GPS Events
GPSConnectedEvent = Event("GPS-Connected")
GPSDisconnectedEvent = Event("GPS-Disconnected")

### Wifi Connected
WifiConnectedEvent = Event("Wifi-Connected")
WifiDisconnectedEvent = Event("Wifi-Disconnected")

### Refuel event
# percent_full=
RefuelEvent = Event("Refuel")

### Car has come to a halt
CarStoppedEvent = Event("CarStopped", suppress_logs=True, debounce_time=10)

########## Incoming Radio Events

# emit() will contain
#   text=
#   duration_secs=
DriverMessageEvent = Event("driver-message")

# emit() will contain
#   flag=(GREEN|YELLOW|RED|BLACK|UNKNOWN)
RaceFlagStatusEvent = Event("flag-status")

# emit() will contain
#   lap_count=
#   ts=
LapInfoEvent = Event("lap-info")

#
RadioReceiveEvent = Event("car-radio-rx")

# A button has been pushed
# button=0   the id of the button that was pushed
ButtonPressEvent = Event("btn", debounce_time=0.25)

# an audio alarm
# message=
AudioAlarmEvent = Event("alrm", debounce_time=60)

# an event indicating the cars position in the race
# pos=
# pos_in_class=
# car_ahead=
# gap=
RacePositionEvent = Event("rpos")

# an event indicating who the car behind us is
# car_behind=
# gap=
RacePersuerEvent = Event("persuer")

# a target lap time has been received from the pits
# target=
SetTargetTimeEvent = Event("target")

# reset the fastest lap
# no args
ResetFastLapEvent = Event("reset-fast-lap")




