

from guizero import Box, Text


# Set a 4-band display box that has the following levels
#  alert = something is wrong, and dangerously high
#  warn = something needs to be actively monitored
#  info = normal operating range
#  low = below operating range
#
#  The intention is to use this for the temperature gauge
#  which will be displayed in both the pit and the car.
#  Other gauges (e.g. oil temp/pressure) could also be done
#  with this mechanism
class AlertBox(Box):

    def __init__(self, parent, **kwargs):
        Box.__init__(self, parent, **kwargs)
        self.orig_bg = parent.bg
        self.low_value = 180
        self.warn_value = 205
        self.error_value = 215

    def set_range(self, low, warn, error):
        self.low_value = low
        self.warn_value = warn
        self.error_value = error

    def update_value(self, value:int):
        self.children[1].value = str(value)
        if value < self.low_value:
            self._low()
        elif value < self.warn_value:
            self._info()
        elif value < self.error_value:
            self._warn()
        else:
            self._alert()

    def _alert(self):
        self.bg = "white"
        self._set_text_color("red")

    def _warn(self):
        self.bg = self.orig_bg
        self._set_text_color("orange")

    def _info(self):
        self.bg = self.orig_bg
        self._set_text_color("green")

    def _low(self):
        self.bg = self.orig_bg
        self._set_text_color("white")

    def _set_text_color(self, color):
        for child in self.children:
            if isinstance(child, Text):
                child.text_color = color
