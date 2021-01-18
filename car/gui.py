from guizero import App, Text, Box, PushButton, Picture

from car.display_providers import *
from car.events import *

import logging
import platform
from python_settings import settings


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


class Gui(EventHandler):

    WIDTH = 800
    HEIGHT = 480
    COL_WIDTH = 266

    def __init__(self):
        self.font = self.__identify_font(platform.system())
        self.root = App("Lemon-Pi",
                       bg="black",
                       width=Gui.WIDTH,
                       height=Gui.HEIGHT)

        self.splash = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, visible=True)
        Box(self.splash, width=Gui.WIDTH, height=100)
        Picture(self.splash, image="resources/images/perplexuslogoslpash.gif")
        Text(self.splash, "Powered by Normtronix", size="24", font=self.font, color="white")

        self.app = Box(self.root, width=Gui.WIDTH, height=Gui.HEIGHT, visible=False)

        col1 = Box(self.app, align="left", width=Gui.COL_WIDTH, height=Gui.HEIGHT)
        col2 = Box(self.app, align="left", width=Gui.COL_WIDTH, height=Gui.HEIGHT)
        col3 = Box(self.app, align="left", width=Gui.COL_WIDTH, height=Gui.HEIGHT)

        # these are invisible displays used to show special case data when the car is pitting
        col4 = Box(self.app, align="left", width=col3.width, height=col3.height, visible=False)
        col5 = Box(self.app, align="left", width=col3.width, height=col3.height, visible=False)

        self.time_widget = self.create_time_widget(col1)
        Box(col1, height=64, width=208)
        self.lap_display = self.create_lap_widget(col1)
        perplexus_logo = Picture(col2, image="resources/images/perplexuslogoclean.gif")
        Box(col2, height=24, width=208)
        self.temp_widget = self.create_temp_widget(col2)
        Box(col2, height=24, width=208)
        self.speed_heading_widget = self.create_speed_widget(col2)
        self.fuel_display = self.create_fuel_widget(col3)

        Box(col2, height=24, width=208)

        # adding obd + gps images
        (self.gps_image, self.obd_image) = self.create_gps_obd_images(col2)
        # add a quit button
        pb = PushButton(col2, image="resources/images/exitbutton.gif", command=self.quit)
        Box(col2, height=24, width=208)

        self.stint_ending_display = self.create_stint_end_instructions(col4)
        self.stint_starting_display = self.create_stint_start_instructions(col5)

        LeaveTrackEvent.register_handler(self)
        StateChangePittedEvent.register_handler(self)
        StateChangeSettingOffEvent.register_handler(self)
        CompleteLapEvent.register_handler(self)
        OBDConnectedEvent.register_handler(self)
        OBDDisconnectedEvent.register_handler(self)
        GPSConnectedEvent.register_handler(self)
        GPSDisconnectedEvent.register_handler(self)

    def present_main_app(self):
        self.splash.destroy()
        self.app.visible = True

    def quit(self):
        self.root.destroy()
        ExitApplicationEvent.emit()

    def handle_event(self, event, **kwargs):
        if event == LeaveTrackEvent:
            self.app.children[2].hide()
            self.app.children[3].show()
            self.app.children[4].hide()
        if event == StateChangePittedEvent:
            self.app.children[2].hide()
            self.app.children[3].hide()
            self.app.children[4].show()
        if event == StateChangeSettingOffEvent:
            self.app.children[2].show()
            self.app.children[3].hide()
            self.app.children[4].hide()

        # go back to the fuel display if we complete a lap and it is not showing.
        if event == CompleteLapEvent and not self.app.children[2].visible:
            self.app.children[2].show()
            self.app.children[3].hide()
            self.app.children[4].hide()

        if event == OBDConnectedEvent:
            self.obd_image.on()

        if event == OBDDisconnectedEvent:
            self.obd_image.off()

        if event == GPSConnectedEvent:
            self.gps_image.on()

        if event == GPSDisconnectedEvent:
            self.gps_image.off()

    def handle_keyboard(self, event_data):
        logger.info("Key Pressed : {}".format(event_data.key))

        # check if we got a CTRL-C
        if ord(event_data.key) == 3:
            self.quit()
            return

        if event_data.key == "s":
            # imitate start/finish behavior
            self.app.children[2].hide()
            self.app.children[3].show()
            self.app.children[4].hide()
        if event_data.key == "f":
            self.app.children[2].hide()
            self.app.children[3].hide()
            self.app.children[4].show()
        if event_data.key == "h":
            self.app.children[2].show()
            self.app.children[3].hide()
            self.app.children[4].hide()
        if event_data.key == 'g':
            self.gps_image.on()
        if event_data.key == 'G':
            self.gps_image.off()
        if event_data.key == 'o':
            self.obd_image.on()
        if event_data.key == 'O':
            self.obd_image.off()

    def display(self):
        self.root.when_key_pressed = self.handle_keyboard
        # on raspberry pi we go full screen
        if platform.system() == "Linux":
            self.root.set_full_screen()
        self.root.after(int(settings.SPLASH_SCREEN_DELAY), self.present_main_app)
        self.root.display()
        # don't put any code here ... the display loop never returns

    def register_temp_provider(self, provider: TemperatureProvider):
        # might need to store in order to cancel
        self.temp_widget.repeat(1000, self.__updateTemp, args=[provider])

    def register_time_provider(self, provider: TimeProvider):
        # might need to store in order to cancel
        self.time_widget.repeat(1000, self.__updateTime, args=[provider])
        self.time_widget.repeat(500, self.__update_time_beat)

    def register_lap_provider(self, provider: LapProvider):
        self.time_widget.repeat(500, self.__updateLap, args=[provider])

    def register_speed_provider(self, provider: SpeedProvider):
        self.speed_heading_widget.repeat(200, self.__updateSpeed, args=[provider])

    def register_fuel_provider(self, provider: FuelProvider):
        self.fuel_display.repeat(1000, self.__updateFuel, args=[provider])

    def create_gps_obd_images(self, parent):
        result = Box(parent, width=208, height=48)
        #result.set_border(4, "darkgreen")
        return (ToggleImage(result, "resources/images/gps_ok.gif", "resources/images/gps_off.gif", align="left"),
                ToggleImage(result, "resources/images/obd_ok.gif", "resources/images/obd_off.gif", align="right"))

    def create_temp_widget(self, parent):
        result = Box(parent, width=212, height=112)
        result.set_border(4, "darkgreen")
        Text(result, "TEMP", size="24", color="white")
        Text(result, "???", size="64", font=self.font, color="white")
        return result

    def create_time_widget(self, parent):
        result = Box(parent, width=212, height=112)
        result.set_border(4, "darkgreen")
        Text(result, "TIME", size="24", font=self.font, color="white")
        Text(result, "hh", size="64", font=self.font, color="white", align="left")
        Text(result, ":", size="32", font=self.font, color="white", align="left")
        Text(result, "mm", size="64", font=self.font, color="white", align="left")
        # Text(result, "ss", size="64", font=self.font, color="grey", align="left")
        return result

    def create_speed_widget(self, parent):
        result = Box(parent, width=212, height=100)
        result.set_border(4, "darkgreen")
        Text(result, "???", size="64", font=self.font, color="white", align="left")
        Text(result, "mph", size="16", color="white", font=self.font, align="left")
        return result

    def create_lap_widget(self, parent):
        result = Box(parent, width=212, height=260)
        result.set_border(4, "darkgreen")
        Text(result, "LAP", size="24", font=self.font, color="white")
        Text(result, "---", size="32", font=self.font, color="white")
        Text(result, "mm:ss", size="32", font=self.font, color="white")
        Box(result, width=200, height=20)
        Text(result, "Last Lap", size="16", font=self.font, color="white")
        Text(result, "mm:ss", size="32", font=self.font, color="white")
        return result

    def create_fuel_widget(self, parent):
        result = Box(parent)
        result.set_border(4, "darkgreen")
        Text(result, "FUEL", size='24', color="lightgreen", font=self.font)
        total_box = Box(result, height=100, width=212)
        Text(total_box, "Total\nUsed", size='16', color="lightgreen", font=self.font, align="left")
        Text(total_box, "--.--", size='32', color="lightgreen", font=self.font, align="left")
        Text(total_box, "Gal", size='16', color="lightgreen", font=self.font, align="left")

        last_hour_box = Box(result, height=100, width=200)
        Text(last_hour_box, "Last\nHour", size='16', color="lightgreen", font=self.font, align="left")
        Text(last_hour_box, "--.--", size='32', color="lightgreen", font=self.font, align="left")
        Text(last_hour_box, "gph", size='16', color="lightgreen", font=self.font, align="left")

        last_lap_box = Box(result, height=100, width=200)
        Text(last_lap_box, "Last\nLap", size='16', color="lightgreen", font=self.font, align="left")
        Text(last_lap_box, "--.--", size='32', color="lightgreen", font=self.font, align="left")
        Text(last_lap_box, "Gal", size='16', color="lightgreen", font=self.font, align="left")

        remaining_box = Box(result, height=100, width=200)
        Text(remaining_box, "Rem.", size='16', color="lightgreen", font=self.font, align="left")
        Text(remaining_box, "--.--", size='32', color="lightgreen", font=self.font, align="left")
        Text(remaining_box, "%", size='16', color="lightgreen", font=self.font, align="left")

        return result

    def create_stint_end_instructions(self, parent):
        result = Box(parent)
        result.set_border(4, "darkgreen")
        Text(result, "INSTRUCTIONS", size='24', color="lightgreen", font=self.font)
        Text(result, "1. Loosen Belts", size='32', color="white", font=self.font)
        Text(result, "2. Undo Belts", size='32', color="white", font=self.font)
        Text(result, "3. Disc. Radio", size='32', color="white", font=self.font)
        Text(result, "4. Stop in Pit", size='32', color="white", font=self.font)
        Text(result, "5. No handbrake", size='32', color="white", font=self.font)
        Text(result, "6. Kill engine", size='32', color="white", font=self.font)
        Text(result, "7. Wheel Off", size='32', color="white", font=self.font)
        Text(result, "8. Get Out!", size='32', color="white", font=self.font)
        return result

    def create_stint_start_instructions(self, parent):
        result = Box(parent)
        result.set_border(4, "darkgreen")
        Text(result, "INSTRUCTIONS", size='24', color="lightgreen", font=self.font)
        Text(result, "1. Adjust Seat", size='32', color="white", font=self.font)
        Text(result, "2. Wheel on", size='32', color="white", font=self.font)
        Text(result, "3. Belts", size='32', color="white", font=self.font)
        Text(result, "4. Radio", size='32', color="white", font=self.font)
        Text(result, "5. Mirrors", size='32', color="white", font=self.font)
        Text(result, "6. Water", size='32', color="white", font=self.font)
        Text(result, "Gloves / Hans?", size='32', color="white", font=self.font)
        return result

    def __updateTemp(self, provider: TemperatureProvider):
        val = provider.get_temp_f()
        widget: Text = self.temp_widget.children[1]
        widget.value = str(val)
        if val < 180 :
            widget.text_color = "white"
            widget.bg = self.app.bg
        elif val < 203 :
            widget.text_color = "green"
            widget.bg = self.app.bg
        elif val < 215 :
            widget.text_color = "orange"
            widget.bg = self.app.bg
        else :
            widget.text_color = "red"
            widget.bg = "white"

    def __updateTime(self, provider: TimeProvider):
        self.time_widget.children[1].value = "{:02d}".format(provider.get_hours())
        self.time_widget.children[3].value = "{:02d}".format(provider.get_minutes())

    def __update_time_beat(self):
        beat : Text = self.time_widget.children[2]
        if beat.text_color == "white":
            beat.text_color = self.app.bg
        else:
            beat.text_color = "white"

    def __updateSpeed(self, provider: SpeedProvider):
        self.speed_heading_widget.children[0].value = "{:02d}".format(provider.get_speed())
        # self.speed_heading_widget.children[2].value = str(provider.get_heading())

    def __updateLap(self, provider: LapProvider):
        self.lap_display.children[1].value = provider.get_lap_count()
        if provider.get_lap_count() != 999:
            minutes = int(provider.get_lap_timer() / 60)
            seconds = int(provider.get_lap_timer()) % 60
            self.lap_display.children[2].value = "{:02d}:{:02d}".format(minutes, seconds)
        if provider.get_last_lap_time() > 0:
            minutes = int(provider.get_last_lap_time() / 60)
            seconds = int(provider.get_last_lap_time()) % 60
            self.lap_display.children[5].value = "{:02d}:{:02d}".format(minutes, seconds)

    def __updateFuel(self, provider: FuelProvider):
        # children offsets:
        total_used_box : Box = self.fuel_display.children[1]
        last_hour_box : Box  = self.fuel_display.children[2]
        last_lap_box : Box = self.fuel_display.children[3]
        remaining_box : Box = self.fuel_display.children[4]

        total_used_box.children[1].value = "{:02.2f}".format(provider.get_fuel_used_ml() / MILLILITRES_PER_GALLON)
        last_hour_box.children[1].value = "{:02.2f}".format(provider.get_fuel_used_last_hour_ml() / MILLILITRES_PER_GALLON)
        last_lap_box.children[1].value = "{:1.02f}".format(provider.get_fuel_used_last_lap_ml() / MILLILITRES_PER_GALLON)
        remaining_box.children[1].value = "{:02d}".format(provider.get_fuel_percent_remaining())

    def __identify_font(self, platform):
        if platform == "Darwin":
            return "arial"
        elif platform == "Linux":
            return "freesans"
        else:
            Exception("no font defined for {}".format(platform))



