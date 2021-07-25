from guizero import Window, App, PushButton


class GuiSettings:

    attrs = {
        'radio_key': {'RADIO_KEY'},
        'race_id': {'RACE_ID'},
        'car_numbers': {'TARGET_CARS', "comma separated"},
        'race_data_send_delay': {'RACE_DATA_SEND_DELAY_SEC'}
    }

    def __init__(self, app: App):
        self.window: Window = Window(app, title="Settings",
                                     bg="charcoal",
                                     width=600, height=400)

        self.lines:[str] = []
        self.race_mode = "Full/Class"
        self.radio_key = "mykey"
        self.race_data_sync_delay = 15
        self.car_number = "0"
        self.race_id = ""

        self.save = PushButton(self.window, text="Save")
        self.cancel = PushButton(self.window, text="Cancel")

    def show(self):
        self.window.show()

    def hide(self):
        self.window.hide()

    def load_local_settings(self):
        lines = []
        with open("lemon_pi/config/local_settings.py") as f:
            lines = f.readlines()
        return lines

    def write_local_settings(self, lines):
        with open("lemon_pi/config/local_settings.py", mode="w") as f:
            f.writelines(lines)

    def update_setting(self, name, value, is_number:bool=False):
        for index, line in enumerate(self.lines):
            l:str = line
            if l.strip().startswith("#"):
                continue
            if l.find(name + " =") or l.find(name + "="):
                if is_number:
                    self.lines[index] = "{} = {}".format(name, value)
                else:
                    self.lines[index] = "{} = '{}'".format(name, value)


FILE_CONTENTS="""

"""