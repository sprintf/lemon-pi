
# Lemon-Pi Development Notes

## Tech Stack

 Python 3.7 (runs best on Raspian)

## Code Organization

The code is split into 3 components:

 - *Shared* : shared code used by both the car amd the pit applications. This mostly involves code to define messages to transmit over the radoi, as well as the radio control logic.
 - *Car* : code that runs on the raspberry-pi (or mac) and talks GPS, OBD and processes and displays this information. 
 - *Pit* : the mac-based application that is used in the pits during a race. It displays telemetry information from the car and can send race position data and messages of encouragement to the driver

In addition to the code are the following directories:

- *config* : config files for both the car and the pit. See Configuration instructions below
- *resources* : contains the gps data for the tracks we race at (or might race at). See the Adding Track Data section below. 
You'll also find the images used in the application in here, as well as some test data.
- *utils* : some half baked utilities that might help with debugging. There's not much of value in here to be honest.  

## Configuration

For the car you will need to configure your fuel tank size if you plan to risk using the dodgy OBD based fuel consumption calculation Lemon-Pi provides.

For the Lora Radio, to avoid getting hit with the radio traffic from all the other teams using this technology (zero) you should choose your own radio frequency and encryption key.

The configuration mechanism we use is [python-settings](https://pypi.org/project/python-settings/)

Edit your own settings into `config/local_settings_car.py` and `config/local_settings_pit.py`

## Adding Track Data

  Track data is stored in [resources/tracks.yaml](resources/tracks.yaml)
  The file is a list of tracks, where each one is of the format:

  ```yaml
  -  name: "Buttonwillow"
     start_finish_coords: "(35.489031,-119.544530),(35.488713,-119.544510)"
     start_finish_direction: "E"
     pit_entry_coords: "(35.488943,-119.547690),(35.489060,-119.547604)"
     pit_entry_direction: "SE"
```

All the coordinates are two coordinates representing a line that is perpendicular to the track. It doesn't matter which order you put the two points in. The direction must be explicitly stated in the `start_finish_direction` field which can be any of the 8 compass points `N, NE, E, SE, S, SW, W, NW`. Google maps is always oriented north, and the direction is the direction of traval for the car (unlike wind direction).

Adding new tracks is simple a metter of adding the name and the start-finish coords and the start-finish direction (at a minimum).
If you add the pit entry coords, then you will also get pitting events sent from the car to the pit (so the team will know you're on your way even if the voice radio is broken). It also prints up the intstructions for the driver who is ending their stint.

The direction is included in this file because it means we can very efficiently determine if you are close to crossing the start-finish (or any other) line. We do very few calculations about the cars position until it is within 100 feet of the line and heading in the right direction. This choice might be a little extra work to setup, but it's handy when we creeta virtual test tracks on the roads around our house, and we can ignore spurious passes when we go the wrong way.

Use google maps to find the GPS coordinates of a point on the planet. Zoom into a location and click and the lat/long coordinates appear. Copy them into your track data file.

By default the car will transmit to the pits each time it crosses the start/finish line. If you want to specify an alternate/additional transmission point you can add a `radio_sync_coords` entry like so:

```yaml
  -  name: "Arlington Test Track"
     start_finish_coords: "(37.926223,-122.295029),(37.926291,-122.294879)"
     start_finish_direction: "SE"
     pit_entry_coords: "(37.928483,-122.297005),(37.928385,-122.297129)"
     pit_entry_direction: "NW"
     radio_sync_coords: "(37.927488,-122.296294),(37.927402,-122.296196)"
     radio_sync_direction: "NE"
   ```

The car automatically selects the closest track when the raspberry pi in-car application boots up.

The full set of track maps that are supported is [here](README-tracks.md)
When you make changes to the tracks.yaml file the new track map is automatically created and the readme page is updated.


## Technical Road Map

  [x] We hope to put this system to the test in April 2021 at Sonoma Raceway at the 24 hours of lemons Sears Pointless race. We will see how ready we are, and how COVID affected the race is. But it gives us a deadline to get things operating.
> Note : it was run at Sonoma; and at Thunderhill. Next it will be run at Buttonwillow in Sept '21
  
  [x] Support for multiple cars within a team is very possible.
> This is now supported.
  
  [ ] We hope to improve the GPS timing .. it's accurate to around 1s now, but more accuracy than that is obviously possible. The GPS hardware we chose, at $11, may not be the very best, so going higher end may help.
> Despite trying several different GPS chips, we've been unable to get anything running and talking to Python faster than 1Hz
  
  [ ] If we find the fuel consumption data is accurate (BIG IF) then we will develop more forecasting functionality into the pit display so that the number of laps possible in the stint and the expected pit time are shown. 
> The fuel consumption data is not accurate enough to be of much use. We'll try it again, but it's less compelling than was hoped.

  [x] The driver instruction text should move into configuration, because it's quite team specific
> The driver instruction text can remind the driver of the pit lane speed, the sequence of stopping and disconnecting things before getting out

  [ ] We will be using an optional button in the car to allow the driver to acknowledge messages, this functionality needs to be built
> We have a button. And RPi can read it and even play a nice noise when it is clicked.  