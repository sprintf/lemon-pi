from guizero import App, Text, Box, PushButton, Picture
import logging

logger = logging.getLogger(__name__)

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

        self.time = self.create_clock(self.main, grid=[0,0])
        self.temp = self.create_temp_gauge(self.main, grid=[1,0])
        self.fuel = self.create_fuel_gauge(self.main, grid=[2,0])
        self.timer = self.create_lap_timer(self.main, grid=[0,1])
        self.lap_fuel = self.create_lap_fuel(self.main, grid=[1,1])
        self.pitting = self.create_pitting_alert(self.main, grid=[1,2])

    def display(self):
        self.root.display()

    def progress(self, percent):
        if percent == 100:
            self.splash.visible = False
            self.main.visible = True
        else:
            self.splash_progress.value = "{}%".format(percent)

    def create_temp_gauge(self, parent, grid):
        result = Box(parent, grid=grid)
        Text(result, "Temp", align="left", color="white")
        self.coolant_temp = Text(result, "???", align="right", color="white")
        return result

    def create_fuel_gauge(self, parent, grid):
        result = Box(parent, grid=grid)
        Text(result, "Fuel %", align="left", color="white")
        self.fuel_percent = Text(result, "???", align="right", color="white")
        return result

    def create_clock(self, parent, grid):
        result = Box(parent, grid=grid)
        self.clock_hour = Text(result, "HH", align="left", color="white")
        Text(result, ":", align="left", color="white")
        self.clock_minute = Text(result, "MM", align="left", color="white")
        return result

    def create_lap_timer(self, parent, grid):
        result = Box(parent, grid=grid)
        Text(result, "lap :", align="left", color="white")
        self.lap_count = Text(result, "NN", align="left", color="white")
        Text(result, "  ", align="left", color="white")
        self.lap_time_minute = Text(result, "MM", align="left", color="white")
        Text(result, ":", align="left", color="white")
        self.lap_time_second = Text(result, "SS", align="left", color="white")
        return result

    def create_lap_fuel(self, parent, grid):
        result = Box(parent, grid=grid)
        self.lap_fuel = Text(result, "NN", align="left", color="white")
        Text(result, "g", align="left", color="white")
        return result

    def create_pitting_alert(self, parent, grid):
        result = Box(parent, grid=grid)
        self.pitting = Text(result, "PITTING", align="left", color="white")
        return result

    def shutdown(self):
        self.root.destroy()

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
