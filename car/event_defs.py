# a simple event framework so we can connect together decoupled logic
from shared.events import Event

# the car is moving
MovingEvent = Event("Moving", suppress_logs=True)

# the car is not moving
NotMovingEvent = Event("NotMoving", suppress_logs=True)

# the car is exiting the race track and entering the pits
LeaveTrackEvent = Event("LeaveTrack")

# a lap has been completed
CompleteLapEvent = Event("CompleteLap")

# a request to exit the application
ExitApplicationEvent = Event("ExitApplication")

# the car should transmit status on radio
RadioSyncEvent = Event("RadioSync")

### State Change Events

# the car is setting off from pits
StateChangeSettingOffEvent = Event("StateChangeSettingOff")

# the car is parked in the pits
StateChangePittedEvent = Event("StateChangePitted")

### OBD Events
OBDConnectedEvent = Event("OBD-Connected")
OBDDisconnectedEvent = Event("OBD-Disconnected")

### GPS Events
GPSConnectedEvent = Event("GPS-Connected")
GPSDisconnectedEvent = Event("GPS-Disconnected")

### Refuel event
RefuelEvent = Event("Refuel")

### Car has come to a halt
CarStoppedEvent = Event("CarStopped", suppress_logs=True)

########## Incoming Radio Events

# emit() will contain
#   text=
#   duration_secs=
DriverMessageEvent = Event("driver-message")

# emit() will contain
#   text=
DriverMessageAddendumEvent = Event("driver-message-addendum")

# emit() will contain
#   flag=(GREEN|YELLOW|RED|BLACK|UNKNOWN)
RaceFlagStatusEvent = Event("flag-status")

# emit() will contain
#   lap_count=
LapInfoEvent = Event("lap-info")


