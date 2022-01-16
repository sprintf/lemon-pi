![Python application](https://github.com/sprintf/lemon-pi/workflows/Python%20application/badge.svg?branch=main)

# Lemon-Pi

<img src="https://24hoursoflemons.com/wp-content/uploads/2017/04/24hours_logo.png" alt="drawing" width="128"/> meets <img src="https://www.raspberrypi.org/wp-content/uploads/2011/10/Raspi-PGB001.png" alt="drawing" width="128"/>

A Raspberry-Pi based dashboard display for endurance car racers.

![image](https://user-images.githubusercontent.com/1510428/103065679-0950b200-456c-11eb-88a1-f50d06d29e8a.png)

Under active hackery, but the basic premise is to solve the following issues
1. provide a display of the current time
2. boldly inform the driver when the engine is overheating
3. let the driver know their position in the race, and the gaps to the cars around them
4. provide a predictive/delta lap timer
5. avoid over-burdening the driver with visual information by making audio announcements in the drivers ear.

In order to achieve the above we use a Raspberry Pi and a screen. The Rpi attaches to the OBD connector in the car and pulls in coolant temperature as well as constantly monitoring MAF in order to infer the fuel usage (that bit is fairly unreliable)

We also use GPS, which allows us to detect when the car crosses the start/finish line, and then show per-lap timing and fuel usage.

We started off using [Lora](https://en.wikipedia.org/wiki/LoRa),
a IoT radio mechanism to send data from the car to the pits and back to the car again,
but it's turning out to be easier to put a phone in the car as a personal
hotspot and just use Wifi from the RPi to the cell phone. Unlike radio,
which is peer-to-peer, we built a server to handle the communications
between the car and the pit. The server is called [Meringue](https://github.com/sprintf/lemon-pi-meringue). 


The target hardware is to use Raspberry Pi in the car and a Mac in the pits,
although all the software is common-or-garden Python so it should run on Windows/Linux in the pits too. 

# Pit Software
Lemon-Pi has a pit module that is designed to run on a Mac. 
It's main job is to pull live race data, and then filter that down to relevant information for the cars on the track, and send that data.
It can also allow text messages to be sent to the driver, in case radio communications break down (that never happens though).
It can display remote telemetry data from the car if OBD is being used (Engine Temp; Fuel Status).
It does some rudimentary calculations to suggest a target laptime each car should be running at in order to make progress through the field.

The pit module can communicate with several cars at the same time. 

If there is no wifi in the paddock, you will need to link the laptop to a mobile phone's hotspot.
If the laptop is not running, or not connected to the internet, the car(s) cannot be informed of their race position.

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

## Lora Radio
 _Being phased out in favor of internet connection in car + pit_
Lostik Lora Radio [Ronoth](https://ronoth.com/products/lostik) you'll need may need one or two of these [cables](https://www.amazon.com/gp/product/B089ZV9Y31/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1) so you can elevate the antenna.

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

Since this is designed for a racing application, we do not want to power it from the main car battery, because during pit stops it is required the kill switch completely disconnects the car battery. We don't want the device needing to reboot, and we want it to keep track of what's been going on (laps completed, historic fuel usage) through a whole day of racing.
The solution is to power the Raspberry Pi from a USB battery pack. [This is the one](https://www.amazon.com/gp/product/B06ZYKMY3G/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) we use to power both the Raspberry Pi and the onboard Go-Pro camera.

It is not possible to run two or three USB devices connected to the Pi as well as having the screen powered.  We are now running power for the screen from a separate source, and are not piggy-backing the screen to the Pi. This has the downside of losing the touch capability of the screen, but does mean the battery can power the Pi for well over 8 hours.

# Lora Radio Learnings

* The maximum packet size of a Lora radio packet is 256 bytes.
* Transmit times / Receive times increase relative to the size of the data being transmitted
* It takes about 6s to send / receive a 256 byte message utilizing 125KHz of bandwidth.
* Although Lora has multi-mile range, it can't go through solid obstructions. In other words it works by 'radio line of sight' although field testing shows it goes through trees and bushes and houses.
* We ended up using protobuf as a message format as it offers very compact on the wire representation, which has brought the lag time down between send and receive to between one and two seconds.
* The radio can either transmit or receive and with multi-second windows when it is doing this we need to keep chatter to a minimum, so we don't send a constant stream of GPS updates, instead we send a summary of each lap including coolant temp, lap time, fuel used on the lap, and total fuel remaining
* Because the start/finish line isn't always the most visible 'radio line of sight' we allow an optional point on the track to be specified and the car sends its data when it hits that point.



