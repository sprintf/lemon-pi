
import logging

from guizero import App, Window, PushButton, CheckBox, TextBox, Box, Text

from lemon_pi.pit.event_defs import CarSettingsEvent, SendTargetTimeEvent


# todo : add columns to display
#   OBD enabled : true / false : will collapse up temp and fuel

class CarSettings:

    def __init__(self, app: App, car_number: str):
        self.window: Window = Window(app, title=f"Car {car_number} Settings",
                                     bg="light gray", # https://wiki.tcl-lang.org/page/Color+Names%2C+running%2C+all+screens
                                     width=600, height=400)

        self.car_number = car_number
        self.target_time = 120

        upper_box = Box(self.window, height=200, width=self.window.width)
        self.chase_mode = CheckBox(upper_box, text="Chase Mode?", command=self.handle_check_box)
        self.chase_mode.text_size = 36

        self.target_car_title = Text(upper_box, "Target Car Number", align="left",
                                     size=36, enabled=self.chase_mode.value)
        self.target_car = TextBox(upper_box, "", width=4, align="left", enabled=self.chase_mode.value)
        self.target_car.text_size = 36
        self.target_car.bg = "white"

        Box(self.window, height=16, width=self.window.width)

        middle_box = Box(self.window, height=48, width=self.window.width)
        self.target_time_title = Text(middle_box, "Target Time:", align="left", size=26)
        self.target_mins = TextBox(middle_box, text="2", width=2, align="left")
        self.target_mins.text_size = 26
        Text(middle_box, ":", align="left")
        self.target_secs = TextBox(middle_box, text="00", width=2, align="left")
        self.target_secs.text_size = 26

        lower_box = Box(self.window, height=48, width=self.window.width)
        self.cancel = PushButton(lower_box, text="Cancel",command=self.handle_close, align="left")
        self.save = PushButton(lower_box, text="Save", command=self.handle_save_and_close, align="right")
        self.hide()

    def handle_check_box(self):
        self.target_car_title.enabled = self.chase_mode.value
        self.target_car.enabled = self.chase_mode.value

    def handle_save_and_close(self):
        try:
            mins = int(self.target_mins.value)
            secs = int(self.target_secs.value)
            self.target_time = mins * 60 + secs
            if self.target_time != self.original_target_time:
                SendTargetTimeEvent.emit(car=self.car_number, target_time=self.target_time)
        except Exception:
            return

        # todo : make sure target car is valid
        if self.chase_mode.value != self.original_chase_mode:
            if self.chase_mode.value == 0:
                # send event saving car settings
                CarSettingsEvent.emit(car=self.car_number, chase_mode=False)
            else:
                # send event saving car settings
                CarSettingsEvent.emit(car=self.car_number, chase_mode=True, target_car=self.target_car.value)
        self.handle_close()

    def handle_close(self):
        self.window.hide()

    def show(self):
        self.original_chase_mode = self.chase_mode.value
        self.original_target_time = self.target_time
        self.window.show()

    def hide(self):
        self.window.hide()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    app = App("bogus main display")
    settings = CarSettings(app, "181")
    settings.show()
    app.display()