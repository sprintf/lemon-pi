from guizero import App, Text, Box, TextBox, PushButton, ListBox, Combo, ButtonGroup

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

NUMBER = 'num'
LAP = 'lap'
POS = 'pos'
CLASS_POS = 'class'
TEMP = 'temp'
LAP_TIME = 'lap_t'
TARGET_TIME = 'target_t'
FUEL = 'fuel'
COMMS = 'comms'

class BigText(Text):

    def __init__(self, parent, text, color="white",**kwargs):
        Text.__init__(self, parent, text, size=32, color=color, **kwargs)


class Gui:

    WIDTH = 840
    HEIGHT = 640

    def __init__(self, target_cars: [str]):

        self.root = App("Lemon-Pit",
                        bg="black",
                        width=Gui.WIDTH,
                        height=Gui.HEIGHT)

        self.target_cars = target_cars
        self.car_data = {}

        self.splash = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, border=200)
        self.splash_progress = Text(self.splash, "0%", size=100, color="green")

        self.main = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, visible=False)
        self.main.set_border(6, color="darkgreen")

        self.title = Box(self.main, align="top", width="fill")
        self.time_widget = self.create_clock(self.title)
        BigText(self.title, "               Lemon Pi Pit", align="left")
        self.race_status = self.create_race_status(self.title, align="right")

        self.car_area = Box(self.main, align="top", width="fill", layout="grid")
        BigText(self.car_area, "Car", color="lightgreen", grid=[0, 0])
        BigText(self.car_area, "Lap", color="lightgreen", grid=[1, 0])
        BigText(self.car_area, "Pos", color="lightgreen", grid=[2, 0])
        BigText(self.car_area, "Class", color="lightgreen", grid=[3, 0])
        BigText(self.car_area, "Last lap", color="lightgreen", grid=[4, 0])
        BigText(self.car_area, "Target", color="lightgreen", grid=[5, 0])
        BigText(self.car_area, "Temp", color="lightgreen", grid=[6, 0])
        BigText(self.car_area, "Fuel", color="lightgreen", grid=[7, 0])
        BigText(self.car_area, "comms", color="lightgreen", grid=[8, 0])
        for row, car in enumerate(self.target_cars):
            self.car_data[car] = {}
            self.car_data[car][NUMBER] = BigText(self.car_area, text=car, grid=[0, row + 1]) # car number
            self.car_data[car][LAP] = BigText(self.car_area, text="0", grid=[1, row + 1]) # lap
            self.car_data[car][POS] = BigText(self.car_area, text="", grid=[2, row + 1]) # pos
            self.car_data[car][CLASS_POS] = BigText(self.car_area, text="", grid=[3, row + 1]) # class pos
            self.car_data[car][LAP_TIME] = BigText(self.car_area, text="HH:MM", grid=[4, row + 1]) # last lap
            self.car_data[car][TARGET_TIME] = BigText(self.car_area, text="", grid=[5, row + 1]) # last lap
            self.car_data[car][TEMP] = self.create_temp_gauge(self.car_area, grid=[6, row + 1]) # temp
            self.car_data[car][FUEL] = BigText(self.car_area, text="?", grid=[7, row + 1]) # fuel
            self.car_data[car][COMMS] = FadingBox(self.car_area, width=32, height=32, grid=[8, row + 1])

        # spacer
        Box(self.main, height=32, width="fill")

        # create a box for communications
        communications = Box(self.main, width="fill", height=172, layout="grid")
        communications.set_border(2, "darkgreen")
        BigText(communications, "Communications", grid=[0, 0])
        self.message = self.create_message_field(communications, grid=[0, 1])
        self.status_message = self.create_status_message(communications, grid=[0, 2])

        # spacer
        Box(self.main, height=32, width="fill")

        self.lap_list: ListBox = self.create_lap_list(self.main)

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
                             car="",
                             position=0,
                             class_position=0,
                             laps=0,
                             last_lap_time=0,
                             ahead="",
                             gap="",
                             flag=""):
        self.__update_position(car=car, position=position, class_position=class_position)
        self.__update_car_data__(car=car, lap_count=laps, last_lap_time=last_lap_time)
        self.car_data[car][LAP].value = laps + 1

    def handle_event(self, event: Event, flag=None, car="", **kwargs):
        if event == RaceStatusEvent:
            self.flag.bg = flag.lower()
            return

        if event == PittingEvent:
            # flash these up and then clear after a while
            self.__show_message(text="Car {} is pitting".format(car), duration_secs=120)
            return

        if event == TelemetryEvent:
            self.__update_car_data__(car=car, **kwargs)
            return

        if event == RadioReceiveEvent:
            self.car_data[car][COMMS].brighten()
            return

        if event == LapCompletedEvent:
            # is this for us? (it could be the following car)
            if car in self.target_cars:
                self.handle_lap_completed(car=car, **kwargs)
            return

        if event == TargetTimeEvent:
            self.__update_target_time(car=car, **kwargs)
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
        BigText(result, " ", align="left")
        BigText(result, "???", align="left")
        BigText(result, "°F", align="right")
        return result

    def create_clock(self, parent):
        result = Box(parent, align="left")
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

    def create_race_status(self, parent, align):
        result = Box(parent, align=align)
        BigText(result, "Race:", align="left")
        self.flag = Box(result, width=32, height=32, align="left")
        self.flag.set_border(4, "grey")
        self.flag.bg = "green"
        return result

    def create_status_message(self, parent, grid):
        result = Box(parent, grid=grid)
        self.status = BigText(result, "", align="left")
        return result

    @staticmethod
    def create_lap_list(parent):
        result = ListBox(parent, scrollbar=True, height=200, width=450)
        result.text_color = "white"
        result.text_size = 32
        result.font = "courier"
        result.append("CAR  LAP  TIME   FUEL")
        return result

    def send_message(self):
        # validate not too long
        text = self.message.children[1].value.strip()
        if len(text) > 0 and len(text) < 30:
            SendMessageEvent.emit(msg=text,
                                  car=self.message.children[2].value)
            self.message.children[1].value = ""
            self.__show_message(text="message sent", duration_secs=1)

    def create_message_field(self, parent, grid):
        result = Box(parent, grid=grid)
        BigText(result, "Send driver message", align="left")
        tb = TextBox(result, "", width=16, align="left")
        tb.text_color = "grey"
        tb.text_size = 32

        target_car = ButtonGroup(result, options=self.target_cars, align="left")
        target_car.bg = "white"
        target_car.text_color = "black"
        target_car.text_size = 32
        if len(self.target_cars) <= 1:
            target_car.visible = False

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

    def __update_car_data__(self, car="", coolant_temp=0, lap_count=0, ts=0,
                            last_lap_time=0, last_lap_fuel=0, fuel_percent=-1):
        minutes = int(last_lap_time / 60)
        seconds = int(last_lap_time) % 60
        entry = "{}  {:03d} {:02d}:{:02d}   {:03d}".format(car.ljust(3), lap_count, minutes, seconds, last_lap_fuel)

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

        self.car_data[car][LAP_TIME].value = "{:02d}:{:02d}".format(minutes, seconds)

        if coolant_temp > 0:
            self.car_data[car][TEMP].update_value(coolant_temp)
        if fuel_percent > 0:
            self.car_data[car][FUEL].value = fuel_percent

    def __update_position(self, car="", position=0, class_position=0):
        self.car_data[car][POS].value = position
        self.car_data[car][CLASS_POS].value = class_position

    def __update_target_time(self, car="", seconds=0.0):
        self.car_data[car][TARGET_TIME].value = "{:02d}:{:02d}".format(int(seconds / 60), int(seconds) % 60)




