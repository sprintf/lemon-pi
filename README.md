![Python application](https://github.com/sprintf/lemon-pi/workflows/Python%20application/badge.svg?branch=main)

# Lemon-Pi

<img src="https://24hoursoflemons.com/wp-content/uploads/2017/04/24hours_logo.png" alt="drawing" width="128"/> meets <img src="https://www.raspberrypi.org/wp-content/uploads/2011/10/Raspi-PGB001.png" alt="drawing" width="128"/>

A Raspberry-Pi based dashboard display for endurance car racers.

![image](https://user-images.githubusercontent.com/1510428/103065679-0950b200-456c-11eb-88a1-f50d06d29e8a.png)

Under active hackery, but the basic premise is to solve the following issues
1. provide a display of the current time
2. provide an indication of the amount of fuel remaining and the rate it is being used
3. boldly inform the driver when the engine is overheating

In order to achieve the above we use a Raspberry Pi and a screen. The Rpi attaches to the OBD connector in the car and pulls in coolant temperature as well as constantly monitoring MAF in order to infer the fuel usage (we don't know if that bit works yet)

We also use GPS, which allows us to detect when the car crosses the start/finish line, and then show per-lap timing and fuel usage.

And we use [Lora](https://en.wikipedia.org/wiki/LoRa), a IoT radio mechanism to send data from the car to the pits and back to the car again.

The target hardware is to use Raspberry Pi in the car and a Mac in the pits, although all the software is common-or-garden Python so it should run on Windows/Linux in the pits too. 

## Raspberry Pi Setup Instructions
[Raspberry Pi specific instructions](README-rpi.md)

# Development Instructions
[Developer README](README-dev.md)

# Hardware

Raspberry Pi Model 3. $35 [Adafruit Link](https://www.adafruit.com/product/3055?src=raspberrypi)

ELEcrow 5" HDMI display. $42.99 [Amazon Link](https://www.amazon.com/gp/product/B013JECYF2/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1)

GPS USB Receiver  $12.99 [Amazon Link](https://www.amazon.com/gp/product/B01MTU9KTF/ref=ppx_yo_dt_b_asin_title_o07_s00?ie=UTF8&psc=1)

OBD USB $16 [Amazon Link](https://www.amazon.com/gp/product/B07MNX424C/ref=ppx_yo_dt_b_asin_title_o04_s00?ie=UTF8&psc=1) 

Lostik Lora Radio [Ronoth](https://ronoth.com/products/lostik) you'll need may need one or two of these [cables](https://www.amazon.com/gp/product/B089ZV9Y31/ref=ppx_yo_dt_b_asin_title_o00_s00?ie=UTF8&psc=1) so you can elevate the antenna.

All the above plug-and-play with the Raspberry Pi.

# Power Considerations

The Raspberry Pi needs a good 2amp power supply. Many USB cables will struggle, and many USB power sources are not rated for this.
I had to buy [these cables](https://www.amazon.com/gp/product/B08FBWFZG4/ref=ppx_yo_dt_b_asin_title_o08_s00?ie=UTF8&psc=1) from Amazon to get rid of the flashing low power indicator.

Since this is designed for a racing application, we do not want to power it from the main car battery, because during pit stops it is required the kill switch completely disconnects the car battery. We don't want the device needing to reboot, and we want it to keep track of what's been going on (laps completed, historic fuel usage) through a whole day of racing.
The solution is to power the Raspberry Pi from a USB battery pack. [This is the one](https://www.amazon.com/gp/product/B06ZYKMY3G/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) we use to power both the Raspberry Pi and the onboard Go-Pro camera.

It is not possible to run two or three USB devices connected to the Pi as well as having the screen powered.  We are now running power for the screen from a separate source, and are not piggy-backing the screen to the Pi. This has the downside of losing the touch capability of the screen, but does mean the battery can power the Pi for well over 8 hours.

# Lora Radio Learnings

* The maximum packet size of a Lora radio packet is 256 bytes.
* Transmit times / Receive times increase relative to the size of the data being transmitted
* It takes about 6s to send / receive a 256 byte message.
* Although Lora has multi-mile range, it can't go through solid obstructions. In other words it works by 'radio line of sight' although field testing shows it goes through trees and bushes and houses.
* We ended up using protobuf as a message format as it offers very compact on the wire representation, which has brought the lag time down between send and receive to about two seconds.
* The radio can either transmit or receive and with multi-second windows when it is doing this we need to keep chatter to a minimum, so we don't send a constant stream of GPS updates, instead we send a summary of each lap including coolant temp, lap time, fuel used on the lap, and total fuel remaining
* Because the start/finish line isn't always the most visible 'radio line of sight' we allow an optional point on the track to be specified and the car sends its data when it hits that point.



