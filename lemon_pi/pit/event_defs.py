import logging

from lemon_pi.shared.events import Event

logger = logging.getLogger(__name__)


# emit() sends out
#   flag=
RaceStatusEvent = Event("race-flag")

# emit() sends out
#   car=
#   laps=
#   position=
#   class_position=
#   ahead=   optional (only if someone ahead)
#   gap=     "-" if nobody ahead
#   last_lap_time=  float value : seconds of last lap
#   flag=
LapCompletedEvent = Event("lap-completed")

# emit() sends out
#   car=
PittingEvent = Event("pitting")

#
#   car=
LeavingPitEvent = Event("entering-track")

# emit() sends out
#   car=
#   ts=
PingEvent = Event("ping")

# emit() sends out
#   car=
#   ts=
#   coolant_temp=
#   lap_count=
#   last_lap_time=
#   fuel_percent=
TelemetryEvent = Event("telemetry")

# emit() sends out
#   car=
#   msg=
SendMessageEvent = Event("send-message")

#   car=
RadioReceiveEvent = Event("pit-radio-rx")

# emit() sends out
# car=
# seconds=
TargetTimeEvent = Event("target-time")

# dumo out the leaderboard to stdout
DumpLeaderboardEvent = Event("dump-leaderboard")

# Car Settings
# car=
# chase_mode= [true/false]
# target_car= [string number if chase mode true]
CarSettingsEvent = Event("car-settings")

# Send a target time to a car
# car=
# target_time=
SendTargetTimeEvent = Event("send-target-time")

# Reset the fast lap on a car's pi
# car=
SendFastLapResetEvent = Event("send-fast-lap-reset")
