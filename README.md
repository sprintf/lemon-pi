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

At a future time, we hope to add onboard digital communications that can relay all this information to the pits each time the car goes past.

Currently, this is all being developed on Mac. Once closer to working we will convert it over to R-pi.

[Raspberry Pi specific instructions](README-rpi.md)