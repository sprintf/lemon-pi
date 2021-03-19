from guizero import App, Text, Box, TextBox, PushButton, ListBox

import logging
from python_settings import settings

from lemon_pi.pit.event_defs import (
    SendMessageEvent,
    RaceStatusEvent,
    PittingEvent,
    LapCompletedEvent,
    TelemetryEvent, DumpLeaderboardEvent, RadioReceiveEvent, TargetTimeEvent
)
from lemon_pi.shared.events import Event
from lemon_pi.shared.gui_components import AlertBox, FadingBox
from lemon_pi.shared.time_provider import TimeProvider

logger = logging.getLogger(__name__)


class BigText(Text):

    def __init__(self, parent, text, **kwargs):
        Text.__init__(self, parent, text, size=32, color="white", **kwargs)


class Gui:

    WIDTH = 1200
    HEIGHT = 800

    def __init__(self):
        self.root = App("Lemon-Pit",
                        bg="black",
                        width=Gui.WIDTH,
                        height=Gui.HEIGHT)

        self.target_car = None
        self.splash = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, border=200)
        self.splash_progress = Text(self.splash, "0%", size=100, color="green")

        self.main = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, layout="grid", visible=False)
        self.main.set_border(6, color="darkgreen")

        row = 0
        self.time_widget = self.create_clock(self.main, grid=[0, row])
        self.race_status = self.create_race_status(self.main, grid=[1, row])
        row += 1
        self.status_message = self.create_status_message(self.main, grid=[0, row])
        row += 1
        self.timer = self.create_lap_timer(self.main, grid=[0, row])
        self.lap_fuel = self.create_lap_fuel(self.main, grid=[1, row])
        row += 1
        Box(self.main, height=64, width="fill", grid=[0, row])
        row += 1
        self.target_time = self.create_target_time(self.main, grid=[0, row])
        self.position_widget = self.create_position_display(self.main, grid=[1, row])
        row += 1
        Box(self.main, height=64, width="fill", grid=[0, row])
        row += 1
        self.temp: AlertBox = self.create_temp_gauge(self.main, grid=[0, row])
        self.fuel = self.create_fuel_gauge(self.main, grid=[1, row])
        row += 1
        Box(self.main, height=64, width="fill", grid=[0, row])
        row += 1
        self.message = self.create_message_field(self.main, grid=[0, row])
        row += 1
        Box(self.main, height=64, width="fill", grid=[0, row])
        row += 1
        self.lap_list: ListBox = self.create_lap_list(self.main, grid=[0, row])

        RaceStatusEvent.register_handler(self)
        PittingEvent.register_handler(self)
        LapCompletedEvent.register_handler(self)
        TelemetryEvent.register_handler(self)
        RadioReceiveEvent.register_handler(self)
        TargetTimeEvent.register_handler(self)

    def display(self):
        self.root.when_key_pressed = self.handle_keyboard
        self.root.display()

    def shutdown(self):
        self.root.destroy()

    def handle_lap_completed(self,
                             position=0,
                             class_position=0,
                             laps=0,
                             last_lap_time=0,
                             ahead="",
                             gap="",
                             flag=""):
        self.__update_position(position=position, class_position=class_position)
        self.__update_car_data__(lap_count=laps, last_lap_time=last_lap_time)
        self.lap_count.value = laps + 1

    def handle_event(self, event: Event, flag=None, car="", **kwargs):
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

        if event == LapCompletedEvent:
            # is this for us? (it could be the following car)
            if car == self.target_car:
                self.handle_lap_completed(**kwargs)
            return

        if event == TargetTimeEvent:
            self.__update_target_time(**kwargs)
            return

    def register_time_provider(self, provider: TimeProvider):
        self.time_widget.repeat(1000, self.__update_time, args=[provider])
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

        if event_data.key == 'D':
            DumpLeaderboardEvent.emit()

    @staticmethod
    def create_temp_gauge(parent, grid):
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

    def create_target_time(self, parent, grid):
        result = Box(parent, grid=grid)
        BigText(result, "Target:", align="left")
        self.target_time_field = BigText(result, "mm:ss", align="left")
        return result

    def create_position_display(self, parent, grid):
        result = Box(parent, grid=grid)
        BigText(result, "Pos:", align="left")
        self.race_position = BigText(result, "P", align="left")
        BigText(result, " class:", align="left")
        self.class_position = BigText(result, "C", align="left")
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

    @staticmethod
    def create_lap_list(parent, grid):
        result = ListBox(parent, grid=grid, scrollbar=True, height=200, width=450)
        result.text_color = "white"
        result.text_size = 32
        result.font = "courier"
        result.append("LAP  TIME   FUEL")
        return result

    def send_message(self):
        # validate not too long
        text = self.message.children[1].value.strip()
        if len(text) > 0 and len(text) < 30:
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
        beat: Text = self.time_widget.children[1]
        if beat.text_color == "white":
            beat.text_color = self.main.bg
        else:
            beat.text_color = "white"

    def __update_time(self, provider: TimeProvider):
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
                            last_lap_time=0, last_lap_fuel=0, fuel_percent=-1):
        minutes = int(last_lap_time / 60)
        seconds = int(last_lap_time) % 60
        entry = "{:03d} {:02d}:{:02d}   {:03d}".format(lap_count, minutes, seconds, last_lap_fuel)

        # always 1 in here for the title row
        if len(self.lap_list.items) > 1:
            top_entry = self.lap_list.items[1]
            top_lap = int(top_entry.split(' ')[0])
            if top_lap == lap_count:
                if last_lap_fuel > 0:
                    self.lap_list.insert(1, entry)
                    self.lap_list.remove(2)
            else:
                self.lap_list.insert(1, entry)
        else:
            self.lap_list.insert(1, entry)
        if coolant_temp > 0:
            self.temp.update_value(coolant_temp)
        if fuel_percent > 0:
            self.fuel_percent.value = fuel_percent

    def __update_position(self, position=0, class_position=0):
        self.race_position.value = position
        self.class_position.value = class_position

    def __update_target_time(self, seconds=0.0):
        self.target_time_field.value = "{:02d}:{:02d}".\
            format(int(seconds / 60), int(seconds) % 60)

    def set_target_car(self, car_number):
        self.target_car = car_number



