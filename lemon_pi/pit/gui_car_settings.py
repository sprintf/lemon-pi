
import logging

from guizero import App, Window, PushButton, CheckBox, TextBox

from lemon_pi.pit.event_defs import CarSettingsEvent

# todo : add columns to display
#   OBD enabled : true / false : will collapse up temp and fuel

class CarSettings:

    def __init__(self, app: App, car_number: str):
        self.window: Window = Window(app, title=f"Car {car_number} Settings",
                                     bg="slate gray", # https://wiki.tcl-lang.org/page/Color+Names%2C+running%2C+all+screens
                                     width=600, height=400)

        self.car_number = car_number

        self.chase_mode = CheckBox(self.window, text="Chase Mode?", command=self.handle_check_box)

        self.target_car_title = TextBox(self.window, "Target Car Number", width=16, align="left", enabled=self.chase_mode.value)
        self.target_car = TextBox(self.window, "", width=16, align="left", enabled=self.chase_mode.value)

        self.save = PushButton(self.window, text="Save", command=self.handle_save_and_close)
        self.cancel = PushButton(self.window, text="Cancel",command=self.handle_close)
        self.hide()

    def handle_check_box(self):
        self.target_car_title.enabled = self.chase_mode.value
        self.target_car.enabled = self.chase_mode.value

    def handle_save_and_close(self):
        # todo : make sure target car is valid
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