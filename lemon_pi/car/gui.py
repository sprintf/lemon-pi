from guizero import App, Text, Box, PushButton, Picture, TextBox, Drawing

from lemon_pi.car.display_providers import *
from lemon_pi.car.event_defs import (

    LeaveTrackEvent, StateChangePittedEvent, StateChangeSettingOffEvent, CompleteLapEvent, OBDConnectedEvent,
    OBDDisconnectedEvent, GPSConnectedEvent, GPSDisconnectedEvent, RaceFlagStatusEvent, DriverMessageEvent,
    ExitApplicationEvent, EnterTrackEvent, RadioReceiveEvent, ButtonPressEvent,
    AudioAlarmEvent, SetTargetTimeEvent, RacePositionEvent, RacePersuerEvent)

import logging
import platform
import random
import time
from python_settings import settings

from lemon_pi.car.state_machine import StateMachine
from lemon_pi.shared.events import EventHandler
from lemon_pi.shared.gui_components import AlertBox, FadingBox
from lemon_pi.shared.time_provider import TimeProvider

logger = logging.getLogger(__name__)

MILLILITRES_PER_GALLON = 3785


class ToggleImage(Picture):

    def __init__(self, parent, on_image, off_image, **kwargs):
        Picture.__init__(self, parent, image=off_image, **kwargs)
        self.on_image = on_image
        self.off_image = off_image

    def on(self):
        self.image = self.on_image

    def off(self):
        self.image = self.off_image


class AlertLight(Drawing):

    def __init__(self, parent, color="yellow"):
        Drawing.__init__(self, parent, width=64, height=64)
        self.bg = "black"
        self.size = 32
        self.adjust = 2
        self.color = color
        self.o = self.oval(32 - self.size, 32 - self.size, 32 + self.size, 32 + self.size, color=self.color)
        self.repeat(50, self.__grow_and_shrink)

    def __grow_and_shrink(self):
        if self.size <= 0:
            self.adjust = 2
        if self.size >= 32:
            self.adjust = -2
        self.size += self.adjust
        self.delete(self.o)
        self.o = self.oval(32 - self.size, 32 - self.size, 32 + self.size, 32 + self.size, color=self.color)


class Gui(EventHandler):

    # these are not really constants, as they get overridden first thing based on
    # settings, but it's ok to think of them ac constants
    WIDTH = 800
    HEIGHT = 480
    COL_WIDTH = 266
    SCALE_FACTOR = 1
    
    TEXT_TINY = 16
    TEXT_SMALL = 24
    TEXT_MED = 32
    TEXT_LARGE = 48
    TEXT_XL = 64

    def __init__(self, width, height):
        Gui.WIDTH = width
        Gui.HEIGHT = height
        Gui.COL_WIDTH = int(width / 3)
        Gui.MESSAGE_ROW_HEIGHT = int(Gui.HEIGHT / 7)
        Gui.SCALE_FACTOR = Gui.WIDTH / 800
        
        if width > 1000:
            Gui.TEXT_TINY = 24
            Gui.TEXT_SMALL = 32
            Gui.TEXT_MED = 48
            Gui.TEXT_LARGE = 64
            Gui.TEXT_XL = 72

        self.start_time = 0
        self.target_time = 0
        self.font = self.__identify_font(platform.system())
        self.root = App("Lemon-Pi",
                        bg="black",
                        width=Gui.WIDTH,
                        height=Gui.HEIGHT)

        self.splash = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, visible=True)
        Box(self.splash, width=Gui.WIDTH, height=int(100 * Gui.SCALE_FACTOR))
        Picture(self.splash, image="resources/images/perplexuslogoslpash.gif")
        Text(self.splash, "Powered by Normtronix", size=Gui.TEXT_SMALL, font=self.font, color="white")

        Box(self.splash, width=Gui.WIDTH, height=int(50 * Gui.SCALE_FACTOR))
        splash_lower = Box(self.splash, width=Gui.WIDTH, height=107, align="right")
        Picture(splash_lower, image="resources/images/argonaut.gif", align="right")
        Text(splash_lower, "in conjunction with", size=Gui.TEXT_SMALL, font=self.font, color="white", align="right")

        self.app = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, visible=False)

        # this is our upper text area
        self.upper_row = Box(self.app, align="top", width=Gui.WIDTH, height=Gui.MESSAGE_ROW_HEIGHT - 16)
        # useful to uncomment this to debug layout
        # self.upper_row.set_border(2, color="red")
        self.msg_area = Text(self.upper_row, "", align="left", size=48, font=self.font, color="white", bg="purple")

        self.col1 = Box(self.app, align="left",
                        width=Gui.COL_WIDTH, height=Gui.HEIGHT - Gui.MESSAGE_ROW_HEIGHT)
        self.col2 = Box(self.app, align="left",
                        width=Gui.COL_WIDTH, height=Gui.HEIGHT - Gui.MESSAGE_ROW_HEIGHT)
        self.col3 = Box(self.app, align="left",
                        width=Gui.COL_WIDTH, height=Gui.HEIGHT - Gui.MESSAGE_ROW_HEIGHT, visible=False)

        # these are invisible displays used to show special case data when the car is pitting
        self.col4 = Box(self.app, align="left", width=self.col3.width, height=self.col3.height, visible=False)
        # these are instructions when next driver getting in
        self.col5 = Box(self.app, align="left", width=self.col3.width, height=self.col3.height, visible=False)
        # this is the predictive lap timer
        self.col6 = Box(self.app, align="left", width=self.col3.width, height=self.col3.height, visible=False)
        # this is the race position display,we're now defaulting to show it rather than fuel
        self.col7 = Box(self.app, align="left", width=self.col3.width, height=self.col3.height, visible=True)

        self.time_widget = self.create_time_widget(self.col1)
        Box(self.col1, height=24, width=int(Gui.COL_WIDTH * 0.8))
        self.lap_display = self.create_lap_widget(self.col1)
        Box(self.col2, height=24, width=int(Gui.COL_WIDTH * 0.8))
        self.temp_widget: AlertBox = self.create_temp_widget(self.col2)
        Box(self.col2, height=24, width=int(Gui.COL_WIDTH * 0.8))
        self.speed_heading_widget = self.create_speed_widget(self.col2)
        self.fuel_display = self.create_fuel_widget(self.col3)

        Box(self.col2, height=24, width=int(Gui.COL_WIDTH * 0.8))

        # adding obd + gps images
        (self.gps_image, self.radio_signal, self.obd_image) = self.create_gps_obd_images(self.col2)
        # add a quit button
        if settings.EXIT_BUTTON_ENABLED:
            PushButton(self.col2, image="resources/images/exitbutton.gif", command=self.quit)
            Box(self.col2, height=24, width=int(Gui.COL_WIDTH * 0.8))

        # this uses high cpu just being invisible : its still growing and shrinking
        #a = AlertLight(self.col2, color="cyan")
        #a.color = "yellow"
        #a.visible = False

        self.stint_ending_display = self.create_instructions(self.col4)
        self.stint_starting_display = self.create_instructions(self.col5)
        self.predictive_lap_timer = self.create_lap_timer(self.col6)
        self.race_position_display = self.create_race_position_display(self.col7)

        LeaveTrackEvent.register_handler(self)
        EnterTrackEvent.register_handler(self)
        StateChangePittedEvent.register_handler(self)
        StateChangeSettingOffEvent.register_handler(self)
        CompleteLapEvent.register_handler(self)
        OBDConnectedEvent.register_handler(self)
        OBDDisconnectedEvent.register_handler(self)
        GPSConnectedEvent.register_handler(self)
        GPSDisconnectedEvent.register_handler(self)
        RaceFlagStatusEvent.register_handler(self)
        DriverMessageEvent.register_handler(self)
        RadioReceiveEvent.register_handler(self)
        SetTargetTimeEvent.register_handler(self)
        RacePositionEvent.register_handler(self)
        RacePersuerEvent.register_handler(self)

    def present_main_app(self):
        # sleep up to 5 seconds
        elapsed_time = time.time() - self.start_time
        logger.info("elapsed time to initialize = {}".format(elapsed_time))
        if elapsed_time < 5:
            time.sleep(5 - elapsed_time)
        self.splash.destroy()
        self.app.visible = True

    def quit(self):
        self.root.destroy()
        ExitApplicationEvent.emit()

    def __remove_message_highlight(self):
        self.msg_area.bg = "black"

    def __remove_message(self):
        self.msg_area.bg = "black"
        self.msg_area.value = ""

    def handle_event(self, event, **kwargs):
        if event == LeaveTrackEvent:
            self._col_display(4)
            return
        if event == StateChangePittedEvent:
            self._col_display(5)
            return
        if event == StateChangeSettingOffEvent or event == EnterTrackEvent:
            self._col_display(3)
            return

        if event == RadioReceiveEvent:
            self.radio_signal.brighten()
            return

        if event == RaceFlagStatusEvent:
            # if it's green, make sure the background of the speed dial is black
            flag = kwargs.get("flag")
            self.speed_heading_widget.text_color = "white"
            if flag == "GREEN":
                self.speed_heading_widget.bg = "black"
            elif flag == "YELLOW":
                self.speed_heading_widget.bg = "yellow"
                self.speed_heading_widget.text_color = "black"
            elif flag == "RED":
                self.speed_heading_widget.bg = "red"
            elif flag == "BLACK":
                self.speed_heading_widget.bg = "dark-blue"
            else:
                logger.warning("unknown flag state : {}".format(flag))
            return

        if event == RacePositionEvent:
            self.__update_race_position(**kwargs)
            self._col_display(7)
            return

        if event == RacePersuerEvent:
            self.__update_persuer_position(**kwargs)
            return

        if event == DriverMessageEvent:
            self.msg_area.text_size = Gui.TEXT_LARGE
            self.msg_area.value = kwargs.get("text")
            duration_secs = kwargs.get("duration_secs")
            self.msg_area.bg = "purple"
            # we cancel any remove message callback to ensure this message
            # stays until it is replaced or stays for the configured time
            self.msg_area.cancel(self.__remove_message)
            self.msg_area.after(3000, self.__remove_message_highlight)
            self.msg_area.after(duration_secs * 1000, self.__remove_message)
            return

        if event == SetTargetTimeEvent:
            self.__update_target_time(kwargs.get("target"))
            return

        # go back to the fuel display if we complete a lap and it is not showing.
        if event == CompleteLapEvent and not self.col3.visible:
            self._col_display(3)
            return

        if event == OBDConnectedEvent:
            self.obd_image.on()
            return

        if event == OBDDisconnectedEvent:
            self.obd_image.off()
            return

        if event == GPSConnectedEvent:
            self.gps_image.on()
            return

        if event == GPSDisconnectedEvent:
            self.gps_image.off()
            return

    def handle_keyboard(self, event_data):
        logger.info("Key Pressed : {}".format(event_data.key))

        # check if we got a CTRL-C
        if ord(event_data.key) == 3:
            self.quit()
            return

        if event_data.key == "s":
            # imitate start/finish behavior
            self._col_display(4)
        if event_data.key == "f":
            self._col_display(5)
        if event_data.key == "h":
            self._col_display(3)
        if event_data.key == 'k':
            self._col_display(6)
        if event_data.key == 'r':
            self._col_display(7)
        if event_data.key == 'g':
            self.gps_image.on()
        if event_data.key == 'G':
            self.gps_image.off()
        if event_data.key == 'o':
            self.obd_image.on()
        if event_data.key == 'O':
            self.obd_image.off()
        if event_data.key == 'l':
            self.__update_lap(randomLapTimeProvider)
            self.__update_predicted_lap(randomLapTimeProvider)
        if event_data.key == 'p':
            self.handle_event(RadioReceiveEvent)
        if event_data.key == 'b':
            ButtonPressEvent.emit(button=0)
        if event_data.key == 'a':
            CompleteLapEvent.emit(lap_time=randomLapTimeProvider.get_last_lap_time(), lap_count=1)
        if event_data.key == 'd':
            DriverMessageEvent.emit(text="plonker, PLONKER!", duration_secs=10)
        if event_data.key == 't':
            if self.target_time == 0:
                self.__update_target_time(67.43)
            else:
                self.__update_target_time(0)

    def _col_display(self, to_show):
        for x in range(3, 8):
            if x == to_show:
                getattr(self, f"col{x}").show()
            else:
                getattr(self, f"col{x}").hide()

    def display(self):
        self.root.when_key_pressed = self.handle_keyboard
        # on raspberry pi we go full screen
        if platform.system() == "Linux":
            self.root.set_full_screen()
        self.start_time = time.time()
        self.root.display()
        # don't put any code here ... the display loop never returns

    def register_temp_provider(self, provider: TemperatureProvider):
        # might need to store in order to cancel
        self.temp_widget.repeat(1000, self.__update_temp, args=[provider])

    def register_time_provider(self, provider: TimeProvider):
        # might need to store in order to cancel
        self.time_widget.repeat(1000, self.__update_time, args=[provider])
        self.time_widget.repeat(500, self.__update_time_beat)

    def register_lap_provider(self, provider: LapProvider):
        self.time_widget.repeat(500, self.__update_lap, args=[provider])
        self.time_widget.repeat(500, self.__update_predicted_lap, args=[provider])

    def register_speed_provider(self, provider: SpeedProvider):
        self.speed_heading_widget.repeat(200, self.__update_speed, args=[provider])

    def register_fuel_provider(self, provider: FuelProvider):
        self.fuel_display.repeat(1000, self.__update_fuel, args=[provider])

    def create_gps_obd_images(self, parent):
        result = Box(parent, width=int(Gui.COL_WIDTH * 0.8), height=int(48 * Gui.SCALE_FACTOR))
        gps = ToggleImage(result,
                          "resources/images/gps_ok.gif",
                          "resources/images/gps_off.gif",
                          align="left")
        Box(result, width=32, height=32, align="left")
        Text(result, "Radio", size=Gui.TEXT_TINY, color="darkgreen", align="left")
        radio = FadingBox(result, width=32, height=32, align="left")
        obd = ToggleImage(result,
                          "resources/images/obd_ok.gif",
                          "resources/images/obd_off.gif",
                          align="right")
        return gps, radio, obd

    def create_temp_widget(self, parent):
        result = AlertBox(parent, width=int(Gui.COL_WIDTH * 0.8), height=int(112 * Gui.SCALE_FACTOR))
        result.set_range(settings.TEMP_BAND_LOW, settings.TEMP_BAND_WARN, settings.TEMP_BAND_HIGH)
        result.set_alarm_cb(lambda: AudioAlarmEvent.emit(message="Engine Overheating"))
        result.set_border(4, "darkgreen")
        Text(result, "TEMP", size=Gui.TEXT_SMALL, color="white")
        Text(result, "???", size=Gui.TEXT_XL, font=self.font, color="white")
        return result

    def create_time_widget(self, parent):
        result = Box(parent, width=int(Gui.COL_WIDTH * 0.8), height=int(112 * Gui.SCALE_FACTOR))
        result.set_border(4, "darkgreen")
        Text(result, "TIME", size=Gui.TEXT_SMALL, font=self.font, color="white")
        Text(result, "hh", size=Gui.TEXT_XL, font=self.font, color="white", align="left")
        Text(result, ":", size=Gui.TEXT_MED, font=self.font, color="white", align="left")
        Text(result, "mm", size=Gui.TEXT_XL, font=self.font, color="white", align="left")
        # Text(result, "ss", size=Gui.TEXT_XL, font=self.font, color="grey", align="left")
        return result

    def create_speed_widget(self, parent):
        result = Box(parent, width=int(Gui.COL_WIDTH * 0.8), height=int(100 * Gui.SCALE_FACTOR))
        result.set_border(4, "darkgreen")
        Text(result, "???", size=Gui.TEXT_XL, font=self.font, color="white", align="left")
        Text(result, "mph", size=Gui.TEXT_TINY, color="white", font=self.font, align="left")
        return result

    def create_lap_widget(self, parent):
        result = Box(parent, width=int(Gui.COL_WIDTH * 0.8), height=int(212 * Gui.SCALE_FACTOR))
        result.set_border(4, "darkgreen")
        lap_box = Box(result)
        Text(lap_box, "LAP", size=Gui.TEXT_SMALL, font=self.font, color="white", align="left")
        Text(lap_box, "---", size=Gui.TEXT_SMALL, font=self.font, color="white", align="left")
        Text(result, "mm:ss", size=Gui.TEXT_LARGE, font=self.font, color="white")
        Box(result, width=200, height=16)
        Text(result, "Last Lap", size=Gui.TEXT_TINY, font=self.font, color="white")
        Text(result, "mm:ss.S", size=Gui.TEXT_LARGE, font=self.font, color="white")
        return result

    def create_fuel_widget(self, parent):
        result = Box(parent)
        result.set_border(4, "darkgreen")
        Text(result, "FUEL", size=Gui.TEXT_SMALL, color="lightgreen", font=self.font)
        remaining_box = Box(result, height=int(100 * Gui.SCALE_FACTOR), width=int(Gui.COL_WIDTH * 0.8))
        Text(remaining_box, "Rem.", size=Gui.TEXT_TINY, color="lightgreen", font=self.font, align="left")
        Text(remaining_box, "--.--", size=Gui.TEXT_MED, color="lightgreen", font=self.font, align="left")
        Text(remaining_box, "%", size=Gui.TEXT_TINY, color="lightgreen", font=self.font, align="left")
        return result

    def create_instructions(self, parent):
        result = Box(parent)
        result.set_border(4, "darkgreen")
        Text(result, "INSTRUCTIONS", size=Gui.TEXT_SMALL, color="lightgreen", font=self.font)
        instructions = TextBox(result, multiline=True,
                               width=parent.width - 8, height=parent.height - 24)
        instructions.text_size = Gui.TEXT_SMALL
        instructions.text_color = "white"
        instructions.font = self.font
        instructions.value = settings.ENTER_PIT_INSTRUCTIONS
        return result

    def create_lap_timer(self, parent):
        result = Box(parent, width=int(Gui.COL_WIDTH * 0.8), height=int(364 * Gui.SCALE_FACTOR))
        result.set_border(4, "darkgreen")
        Text(result, "PREDICTED", size=Gui.TEXT_SMALL, color="lightgreen", font=self.font)
        # child [1]
        Text(result, "mm:ss", size=Gui.TEXT_XL, font=self.font, color="white")

        # spacer
        Box(result, width=12 * Gui.SCALE_FACTOR, height=24, align="left")

        # Delta timer
        Text(result, "DELTA", size=Gui.TEXT_SMALL, color="lightgreen", font=self.font)
        # child [4]
        Text(result, "0 s", size=Gui.TEXT_XL, font=self.font, color="white")

        # spacer
        Box(result, width=12 * Gui.SCALE_FACTOR, height=24, align="left")

        Text(result, "BEST", size=Gui.TEXT_SMALL, color="lightgreen", font=self.font)
        # child [7]
        Text(result, "mm:ss", size=Gui.TEXT_LARGE, font=self.font, color="white")

        return result

    def create_race_position_display(self, parent):
        result = Box(parent, width=int(Gui.COL_WIDTH * 0.8), height=int(364 * Gui.SCALE_FACTOR))
        result.set_border(4, "lightgreen")
        # child 0 = position
        Text(result, "P??", size=Gui.TEXT_LARGE, font=self.font, color="white")
        Box(result, width=24 * Gui.SCALE_FACTOR, height=48)
        # child 2 = parent
        container1 = Box(result, width=parent.width, height=80)
        Text(container1, "Ahead: #", size=Gui.TEXT_TINY, font=self.font, color="grey", align="left")
        # child [2][1] = car ahead
        Text(container1, "?? ", size=Gui.TEXT_MED, font=self.font, color="white", align="left")
        container2 = Box(result, width=parent.width, height=48)
        Text(container2, "By: ", size=Gui.TEXT_SMALL, font=self.font, color="grey", align="left")
        # child [3][1] = gap
        Text(container2, "?? ", size=Gui.TEXT_MED, font=self.font, color="white", align="left")
        Box(result, width=parent.width, height=48)
        # child [5]
        container3 = Box(result, width=parent.width, height=72)
        Text(container3, "Behind: #", size=Gui.TEXT_TINY, font=self.font, color="grey", align="left")
        # child [5][1] car behind
        Text(container3, "?? ", size=Gui.TEXT_MED, font=self.font, color="white", align="left")
        container4 = Box(result, width=parent.width, height=48)
        Text(container4, "By: ", size=Gui.TEXT_SMALL, font=self.font, color="grey", align="left")
        # child [6][1] gap to car behind
        Text(container4, "?? ", size=Gui.TEXT_MED, font=self.font, color="white", align="left")
        return result

    def __update_race_position(self, pos=0, pos_in_class=0, car_ahead="0", gap="?"):
        panel = self.col7.children[0]
        if pos == pos_in_class:
            panel.children[0].value = f"P{pos}"
            panel.children[0].text_size = Gui.TEXT_LARGE
        else:
            panel.children[0].value = f"P{pos_in_class}({pos})"
            panel.children[0].text_size = Gui.TEXT_MED
        panel.children[2].children[1].value = car_ahead
        panel.children[3].children[1].value = gap
        panel.children[5].children[1].value = ""
        panel.children[6].children[1].value = ""

    def __update_persuer_position(self, car_behind=0, gap="?"):
        panel = self.col7.children[0]
        panel.children[5].children[1].value = car_behind
        panel.children[6].children[1].value = gap

    def __update_temp(self, provider: TemperatureProvider):
        val = provider.get_temp_f()
        self.temp_widget.update_value(val)

    def __update_time(self, provider: TimeProvider):
        self.time_widget.children[1].value = "{:02d}".format(provider.get_hours())
        self.time_widget.children[3].value = "{:02d}".format(provider.get_minutes())

    def __update_time_beat(self):
        beat : Text = self.time_widget.children[2]
        if beat.text_color == "white":
            beat.text_color = self.app.bg
        else:
            beat.text_color = "white"

    def __update_speed(self, provider: SpeedProvider):
        self.speed_heading_widget.children[0].value = "{:02d}".format(provider.get_speed())
        # self.speed_heading_widget.children[2].value = str(provider.get_heading())

    def __update_lap(self, provider: LapProvider):
        self.lap_display.children[0].children[1].value = provider.get_lap_count()
        if provider.get_lap_count() != 999:
            minutes = int(provider.get_lap_timer() / 60)
            seconds = int(provider.get_lap_timer()) % 60
            self.lap_display.children[1].value = "{:02d}:{:02d}".format(minutes, seconds)
        if provider.get_last_lap_time() > 0:
            ll = provider.get_last_lap_time()
            minutes = int(ll / 60)
            seconds = int(ll) % 60
            tenths = int((ll - int(ll)) * 10)
            self.lap_display.children[4].value = "{:02d}:{:02d}.{:01d}".format(minutes, seconds, tenths)

    def __update_target_time(self, target_time: float):
        self.target_time = target_time
        outer_box = self.col6.children[0]
        if self.target_time != 0:
            outer_box.children[6].value = "TARGET"
            self.__display_time(self.target_time, outer_box.children[7])
        else:
            outer_box.children[6].value = "BEST"
            self.__display_time(0, outer_box.children[7])

    def __update_predicted_lap(self, provider: LapProvider):
        predicted = provider.get_predicted_lap_time()
        target_lap = self.target_time or provider.get_best_lap_time()

        outer_box = self.col6.children[0]

        if predicted:
            # if we're on track and getting predictions then show them
            if StateMachine.is_on_track() and not self.col6.visible:
                self._col_display(6)
            minutes = int(predicted / 60)
            seconds = int(predicted % 60)
            outer_box.children[1].value = "{:02d}:{:02d}".format(minutes, seconds)

            if target_lap:
                delta = predicted - target_lap
                outer_box.children[4].value = f"{delta:0.1f} s"
                if delta < -1:
                    outer_box.children[4].text_color = "white"
                    outer_box.children[4].bg = "purple"
                elif delta < 1:
                    outer_box.children[4].text_color = "green"
                    outer_box.children[4].bg = "black"
                elif delta < 2:
                    outer_box.children[4].text_color = "white"
                    outer_box.children[4].bg = "black"
                else:
                    outer_box.children[4].text_color = "yellow"
                    outer_box.children[4].bg = "black"
            else:
                outer_box.children[4].value = "? s"
                outer_box.children[4].text_color = "grey"
                outer_box.children[4].bg = "black"

        if target_lap:
            self.__display_time(target_lap, outer_box.children[7])

    @staticmethod
    def __display_time(seconds:float, text_box:Text):
        minutes = int(seconds / 60)
        seconds = int(seconds % 60)
        text_box.value = "{:02d}:{:02d}".format(minutes, seconds)

    def __update_fuel(self, provider: FuelProvider):
        # children offsets:
        remaining_box : Box = self.fuel_display.children[1]
        remaining_box.children[1].value = "{:02d}".format(provider.get_fuel_percent_remaining())

    def __identify_font(self, platform):
        if platform == "Darwin":
            return "arial"
        elif platform == "Linux":
            return "freesans"
        else:
            Exception("no font defined for {}".format(platform))


# test classes
class RandomLapTimeProvider(LapProvider):

    def __init__(self):
        self.start_time = time.time()

    def get_last_lap_time(self) -> float:
        return random.randint(100000, 300000) / 1000

    def get_predicted_lap_time(self) -> float:
        return 200 + random.randint(-2000, 2000) / 1000

    def get_lap_timer(self) -> int:
        return int(time.time() - self.start_time)

    def get_lap_count(self) -> int:
        return 145

    def get_best_lap_time(self) -> float:
        return 200 + random.randint(-2000, 2000) / 1000

randomLapTimeProvider = RandomLapTimeProvider()

