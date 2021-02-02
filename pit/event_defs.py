import logging

from shared.events import Event

logger = logging.getLogger(__name__)


# emit() sends out
#   flag=
RaceStatusEvent = Event("race-flag")

# emit() sends out
#   car=
#   laps=
#   position=
#   ahead=   optional (only if someone ahead)
#   gap=     "-" if nobody ahead
#   last_lap_time=  text of lap time
LapCompletedEvent = Event("lap-completed")

# emit() sends out
#   car=
PittingEvent = Event("pitting")

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
#   last_lap_fuel=
#   fuel_percent=
TelemetryEvent = Event("telemetry")

# emit() sends out
#   car=
#   msg=
SendMessageEvent = Event("send-message")