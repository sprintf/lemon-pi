from guizero import App, Text, Box, TextBox, PushButton, ListBox

import logging
from python_settings import settings

from lemon_pi.pit.event_defs import (
    SendMessageEvent,
    RaceStatusEvent,
    PittingEvent,
    LapCompletedEvent,
    TelemetryEvent, DumpLeaderboardEvent, RadioReceiveEvent
)
from lemon_pi.shared.events import Event
from lemon_pi.shared.gui_components import AlertBox, FadingBox
from lemon_pi.shared.time_provider import TimeProvider

logger = logging.getLogger(__name__)


presses = 0

class BigText(Text):

    def __init__(self, parent, text, **kwargs):
        Text.__init__(self, parent, text, size=32, color="white", **kwargs)


class Gui():

    WIDTH = 1200
    HEIGHT = 800

    def __init__(self):
        self.root = App("Lemon-Pit",
                       bg="black",
                       width=Gui.WIDTH,
                       height=Gui.HEIGHT)

        self.splash = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, border=200)
        self.splash_progress = Text(self.splash, "0%", size=100, color="green")

        self.main = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, layout="grid", visible=False)
        self.main.set_border(6, color="darkgreen")

        self.time_widget = self.create_clock(self.main, grid=[0,0])
        self.race_status = self.create_race_status(self.main, grid=[1,0])
        self.status_message = self.create_status_message(self.main, grid=[0, 1])

        self.timer = self.create_lap_timer(self.main, grid=[0,2])
        self.lap_fuel = self.create_lap_fuel(self.main, grid=[1,2])

        Box(self.main, height=64, width="fill", grid=[0,3])

        self.temp:AlertBox = self.create_temp_gauge(self.main, grid=[0,4])
        self.fuel = self.create_fuel_gauge(self.main, grid=[1,4])

        Box(self.main, height=64, width="fill", grid=[0,5])

        self.message = self.create_message_field(self.main, grid=[0,6])

        Box(self.main, height=64, width="fill", grid=[0,7])

        self.lap_list:ListBox = self.create_lap_list(self.main, grid=[0,8])

        RaceStatusEvent.register_handler(self)
        PittingEvent.register_handler(self)
        LapCompletedEvent.register_handler(self)
        TelemetryEvent.register_handler(self)
        RadioReceiveEvent.register_handler(self)

    def display(self):
        self.root.when_key_pressed = self.handle_keyboard
        self.root.display()

    def shutdown(self):
        self.root.destroy()

    def handle_event(self, event:Event, flag=None, car="", **kwargs):
        if event == RaceStatusEvent:
            self.flag.bg = flag.lower()
            return

        if event == PittingEvent:
            # flash these up and then clear after a while
            self.__show_message(text="Car {} is pitting".format(car), duration_secs=120)
            return

        if event == TelemetryEvent:
            self.__update_car_data__(**kwargs)
            return

        if event == RadioReceiveEvent:
            self.radio_signal.brighten()
            return

    def register_time_provider(self, provider:TimeProvider):
        self.time_widget.repeat(1000, self.__updateTime, args=[provider])
        self.time_widget.repeat(500, self.__update_time_beat)

    def progress(self, percent):
        if percent == 100:
            self.splash.visible = False
            self.main.visible = True
        else:
            self.splash_progress.value = "{}%".format(percent)

    def handle_keyboard(self, event_data):
        logger.info("Key Pressed : {}".format(event_data.key))

        # check if we got a CTRL-C
        if ord(event_data.key) == 3:
            self.shutdown()
            return

        if event_data.key == "l":
            global presses
            self.__update_car_data__(car="181",
                                     lap_count=1 + presses,
                                     coolant_temp=190 + presses,
                                     last_lap_time=124 - presses,
                                     last_lap_fuel=312 + presses,
                                     fuel_percent=98 - presses)
            presses += 1

        if event_data.key == 'd':
            DumpLeaderboardEvent.emit()

    def create_temp_gauge(self, parent, grid):
        result = AlertBox(parent, grid=grid)
        result.set_range(settings.TEMP_BAND_LOW, settings.TEMP_BAND_WARN, settings.TEMP_BAND_HIGH)
        BigText(result, "Temp", align="left")
        BigText(result, "???", align="right")
        return result

    def create_fuel_gauge(self, parent, grid):
        result = Box(parent, grid=grid)
        BigText(result, "Fuel %", align="left")
        self.fuel_percent = BigText(result, "???", align="right")
        return result

    def create_clock(self, parent, grid):
        result = Box(parent, grid=grid)
        self.clock_hour = BigText(result, "HH", align="left")
        BigText(result, ":", align="left")
        self.clock_minute = BigText(result, "MM", align="left")
        return result

    def create_lap_timer(self, parent, grid):
        result = Box(parent, grid=grid)
        BigText(result, "lap :", align="left")
        self.lap_count = BigText(result, "NN", align="left")
        BigText(result, "  ", align="left")
        self.lap_time_minute = BigText(result, "MM", align="left")
        BigText(result, ":", align="left")
        self.lap_time_second = BigText(result, "SS", align="left")
        return result

    def create_lap_fuel(self, parent, grid):
        result = Box(parent, grid=grid)
        self.lap_fuel = BigText(result, "NN", align="left")
        BigText(result, "g", align="left")
        return result

    def create_race_status(self, parent, grid):
        result = Box(parent, grid=grid)
        BigText(result, "Race:", align="left")
        self.flag = Box(result, width=32, height=32, align="left")
        self.flag.set_border(4, "grey")
        self.flag.bg = "green"

        BigText(result, "Radio:", align="left")
        self.radio_signal = FadingBox(result, width=32, height=32, align="left")
        return result

    def create_status_message(self, parent, grid):
        result = Box(parent, grid=grid)
        self.status = BigText(result, "", align="left")
        return result

    def create_lap_list(self, parent, grid):
        result = ListBox(parent, grid=grid, scrollbar=True, height=200, width=450)
        result.text_color = "white"
        result.text_size = 32
        result.font = "courier"
        result.append("LAP  TIME   FUEL")
        return result

    def send_message(self):
        # validate not too long
        text = self.message.children[1].value.strip()
        if len(text) > 0 and len(text) < 20:
            SendMessageEvent.emit(msg=self.message.children[1].value, car=settings.TARGET_CAR)
            self.message.children[1].value = ""
            self.__show_message(text="message sent", duration_secs=1)

    def create_message_field(self, parent, grid):
        result = Box(parent, grid=grid)
        BigText(result, "Send driver message", align="left")
        tb = TextBox(result, "", width=16, align="left")
        tb.text_color = "grey"
        tb.text_size = 32
        pb = PushButton(result, text="Send", align="left")
        pb.when_clicked = self.send_message
        return result

    def __update_time_beat(self):
        beat : Text = self.time_widget.children[1]
        if beat.text_color == "white":
            beat.text_color = self.main.bg
        else:
            beat.text_color = "white"

    def __updateTime(self, provider: TimeProvider):
        self.time_widget.children[0].value = "{:02d}".format(provider.get_hours())
        self.time_widget.children[2].value = "{:02d}".format(provider.get_minutes())

    def __remove_message(self):
        self.status.bg = "black"
        self.status.value = ""

    def __remove_message_highlight(self):
        self.status.bg = "black"

    def __show_message(self, text="", duration_secs=10):
        self.status.cancel(self.__remove_message)
        # if the message is showing for a while then flash up a highlight
        if duration_secs > 10:
            self.status.after(2000, self.__remove_message_highlight)
        self.status.after(duration_secs * 1000, self.__remove_message)
        self.status.value = text

    def __update_car_data__(self, car="", coolant_temp=0, lap_count=0,
                            last_lap_time=0, last_lap_fuel=0, fuel_percent = -1):
        minutes = int(last_lap_time / 60)
        seconds = last_lap_time % 60
        entry = "{:03d} {:02d}:{:02d}   {:03d}".format(lap_count, minutes, seconds, last_lap_fuel )
        self.lap_list.insert(1, entry)
        self.temp.update_value(coolant_temp)
        self.fuel_percent.value = fuel_percent

# items to display
# last time we heard from car
# race flag color
# car data :
#    temp; last lap; laps; recent laps
#    fuel used + lap time
# fuel remaining
# est pit time
#   mean fuel used over last 3 laps
# pitting flag

# Race overall:
#  time
#  flag status
#  message board <message sent> | <car 181 pitting>


