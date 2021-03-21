

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
        # a value of -1 is returned if the temperate is more than
        # a minute old
        if value > 0:
            self.children[1].value = str(value)
        else:
            self.children[1].value = '?'
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


# a Fading Box starts off as an empty box. When it is told
# to brighten() then it does so and then fades darker over
# a period of time. We use this to indicate the
# freshness of radio pings and other radio receives
class FadingBox(Box):

    def __init__(self, parent, bright=0xffffff, dim=0x202020, **kwargs):
        Box.__init__(self, parent, **kwargs)
        self.bright_rgb = self.__split_rgb(bright)
        self.dim_rgb = self.__split_rgb(dim)
        self.bg = self.dim_rgb
        self.set_border(4, "grey")
        self.repeat(10000, self.__fade)

    def brighten(self):
        self.bg = self.bright_rgb

    def __fade(self):
        rgb_hex = int(self.bg[1:], 16)
        (r, g, b) = self.__split_rgb(rgb_hex)
        if r > self.dim_rgb[0]:
            self.bg = (r - 16, g - 16, b - 16)

    def __split_rgb(self, rgb_value):
        r = (rgb_value & 0xff0000) >> 16
        g = (rgb_value & 0xff00) >> 8
        b = rgb_value & 0xff
        return r, g, b