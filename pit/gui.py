from guizero import App, Text, Box, TextBox, PushButton, ListBox

import logging

from pit.event_defs import SendMessageEvent, RaceStatusEvent, PittingEvent
from shared.events import Event
from shared.time_provider import TimeProvider

logger = logging.getLogger(__name__)


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
        self.main.set_border(6, color="green")

        self.time_widget = self.create_clock(self.main, grid=[0,0])
        self.race_status = self.create_race_status(self.main, grid=[1,0])
        self.status_message = self.create_status_message(self.main, grid=[0, 1])

        self.timer = self.create_lap_timer(self.main, grid=[0,2])
        self.lap_fuel = self.create_lap_fuel(self.main, grid=[1,2])

        Box(self.main, height=64, width="fill", grid=[0,3])

        self.temp = self.create_temp_gauge(self.main, grid=[0,4])
        self.fuel = self.create_fuel_gauge(self.main, grid=[1,4])

        Box(self.main, height=64, width="fill", grid=[0,5])

        self.message = self.create_message_field(self.main, grid=[0,6])

        Box(self.main, height=64, width="fill", grid=[0,7])

        self.lap_list = self.create_lap_list(self.main, grid=[0,8])

        RaceStatusEvent.register_handler(self)
        PittingEvent.register_handler(self)

    def display(self):
        self.root.display()

    def shutdown(self):
        self.root.destroy()

    def handle_event(self, event:Event, flag=None, car=""):
        if event == RaceStatusEvent:
            self.flag.bg = flag.lower()
            return

        if event == PittingEvent:
            # flash these up and then clear after a while
            self.__show_message(text="Car {} is pitting".format(car), duration_secs=120)
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

    def create_temp_gauge(self, parent, grid):
        result = Box(parent, grid=grid)
        BigText(result, "Temp", align="left")
        self.coolant_temp = BigText(result, "???", align="right")
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
        self.flag = Box(result, width=64, height=48)
        self.flag.bg = "green"
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
        result.append(" {:2d} {:2d}:{:2d} {:2.2f}".format(1, 1, 57, 326.5))
        return result

    def send_message(self):
        # validate not too long
        text = self.message.children[1].value.strip()
        if len(text) > 0 and len(text) < 20:
            SendMessageEvent.emit(msg=self.message.children[1].value)
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


