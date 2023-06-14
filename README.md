![Python application](https://github.com/sprintf/lemon-pi/workflows/Python%20application/badge.svg?branch=main)

# Lemon-Pi

<img src="https://24hoursoflemons.com/wp-content/uploads/2017/04/24hours_logo.png" alt="drawing" width="128"/> meets <img src="https://www.raspberrypi.org/wp-content/uploads/2011/10/Raspi-PGB001.png" alt="drawing" width="128"/>

A Raspberry-Pi based dashboard display for endurance car racers.

<img width="138" alt="image" src="https://github.com/sprintf/lemon-pi/assets/1510428/6e947d3c-ba20-4fdb-93ec-d1b09f2867f6">

Under active hackery, but the basic premise is to solve the following issues
1. provide a display of the current time
2. boldly inform the driver when the engine is overheating
3. let the driver know their position in the race, and the gaps to the cars around them
4. provide a predictive/delta lap timer
5. avoid over-burdening the driver with visual information by making audio announcements in the drivers ear.

In order to achieve the above we use a Raspberry Pi, a screen and a Wifi connection. The Rpi attaches to the OBD connector in the car and constantly pulls in coolant temperature and displays it. The time is provided by the Wifi connection and is generally very accurate. 

We also use GPS, which allows us to detect when the car crosses the start/finish line, and then show per-lap timing.

We put a phone in the car as a personal hotspot and just use Wifi from the RPi to the cell phone. Then we built a server to handle the communications
between the car and the pit. The server is called [Meringue](https://github.com/sprintf/lemon-pi-meringue). 

# Pit Integration
Lemon-Pi also works with a Slack integration in order to inform team mates when the car is pitting, as well as pinging the lap time and engine temperature as each lap is completed. The slack integration easily allows team mates and support staff to know when the car is on the track or in the pits. 
The Pit Integration also allows text messages to be sent to the driver, in case radio communications break down (that never happens though).

## Raspberry Pi Setup Instructions
[Raspberry Pi specific instructions](README-rpi.md)

# Development Instructions
[Developer README](README-dev.md)

# Hardware

## Computer
Raspberry Pi Model 3+. $35 [Adafruit Link](https://www.adafruit.com/product/3055?src=raspberrypi)

> **Note**
It's quite hard to find the model 3+ now. You can get a model 4 which is more readily available and the same price, but your experience with the battery used here may vary. The RPi 4 is known to be more power hungry than the 3/3+

## Display Options

Sunfounder 7" HDMI display. $65.99 [Amazon Link](https://www.amazon.com/SunFounder-Inch-Monitor-HDMI-Raspberry/dp/B073GYBS93)

> Note : There's a quite nice [ELEcrow 5" HDMI display](https://www.amazon.com/gp/product/B013JECYF2/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1) but it can only run on USB power andis not bright enough. Use a 12v powered display or it will not be bright enough.


## GPS
GPS USB Receiver $12.99 [Amazon Link](https://www.amazon.com/gp/product/B01MTU9KTF/ref=ppx_yo_dt_b_asin_title_o07_s00?ie=UTF8&psc=1)

Adafruit Ultimate USB GPS $29.95 [Digi-Key](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4279/10263862?s=N4IgjCBcoLQBxVAYygMwIYBsDOBTANCAPZQDa4ArAEwIC6AvvYVWSACxUDsAnCA0A)
> *** Note *** In theory this receiver can operate at 10Hz, providing a lot more GPS data. However, the fastest we've been able to get this working is 2.5Hz.

> DO NOT USE 
Global Sat BU3-353S4 $28.38 [Amazon Link](https://www.amazon.com/GlobalSat-BU-353-S4-USB-Receiver-Black/dp/B008200LHW) as it doesn't work so well with gpsd on the RPi. 

## OBD 
OBD USB $16 [Amazon Link](https://www.amazon.com/gp/product/B07MNX424C/ref=ppx_yo_dt_b_asin_title_o04_s00?ie=UTF8&psc=1) 

All the above plug-and-play with the Raspberry Pi.

## Sound Mixing Hardware
Mini Mixer $8.95 [Ebay](https://www.ebay.com/itm/174795427830)

> This is useful to provide an easy to reach volume control for the driver. This can mix input from the Radio on one channel, and the RPi on the other channel, and mix the two audio sources into the drivers headset. If your drivers use helmets with a microphone, you will need to custom wire the microphone around this contraption and back to the radio. We use Nascar wiring for our headset adapters, and this didn't provide too difficult.

# Tracks Currently Supported

Almost ALL the tracks that are raced by 24 Hours of Lemons are now supported.
If yours isn't or the configuration doesn't match, file an Issue.
The tracks that are currently supported is [here](README-tracks.md)

# Power Considerations

The Raspberry Pi needs a good 2amp power supply. Many USB cables will struggle, and many USB power sources are not rated for this.
I had to buy [these cables](https://www.amazon.com/gp/product/B08FBWFZG4/ref=ppx_yo_dt_b_asin_title_o08_s00?ie=UTF8&psc=1) from Amazon to get rid of the flashing low power indicator.

Since this is designed for a racing application, we do not want to power it from the main car battery, because during pit stops it is required the kill switch completely disconnects the car battery. We don't want the device needing to reboot, and we want it to keep track of what's been going on (laps completed, predictive lap timing data) through a whole day of racing.
The solution is to power the Raspberry Pi from a USB battery pack. [This is the one](https://www.amazon.com/gp/product/B06ZYKMY3G/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) we use to power both the Raspberry Pi and the onboard Go-Pro camera.

It is not possible to run two or three USB devices connected to the Pi as well as having the screen powered.  We are now running power for the screen from a separate source, and are not piggy-backing the screen to the Pi. This has the downside of losing the touch capability of the screen, but does mean a 16,000mAh battery can power the Pi for more than 12 hours.



