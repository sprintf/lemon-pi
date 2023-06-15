## Developing/Running on Raspberry Pi

Start with Raspberry Pi OS Debian Bullseye with Pi Desktop.
You can install this with Raspberry Pi Imager onto a SD card.
Fire up the Raspberry Pi, apply OS updates, and then bring up a terminal and follow the instructions below

1. install python 3.8
Follow instructions at (rpi-pyenv)[https://www.samwestby.com/tutorials/rpi-pyenv]
```sh
pyenv global 3.8.17
```

2. install gpsd, git etc

```sh
sudo apt-get install git gpsd gpsd-clients espeak
```

3. fetch the git repos

```sh
git clone https://github.com/sprintf/lemon-pi.git
git clone https://github.com/sprintf/lemon-pi-protos.git
```

4. cd into the lemon-pi directory

```sh
cd lemon-pi
```

5. setup venv

```sh
python3 -m venv venv
. venv/bin/activate
python -m pip install --upgrade pip
pip install --upgrade setuptools
pip install -r requirements.txt
```
If you get a failure with Pillow, then delete it from requirements.txt ... it's a test/util dependency and not needed at runtime on the RPi.
After deleting it, run `pip install -r requirements.txt` again and it will succeed

7. create some logging/state directories

```sh

sudo mkdir /var/lib/lemon-pi
sudo chmod a+w /var/lib/lemon-pi
```

8. launch the lemon-pi application

```sh
./bin/start-car.sh
```

## Autostarting 

Create a file called `/etc/xdg/autostart/lemon-pi.desktop`

Put this into the contents of the file:

```sh
[Desktop Entry]
Type=Application
Name=Lemon-Pi
Comment=Start Lemon-Pi OBD GPS display
NoDisplay=False
Exec=/usr/bin/lxterminal -e /home/pi/lemon-pi/bin/start-car.sh
NotShowIn=GNOME;KDE;XFCE;
```

## Setting the screen size and preventing screen saving
If using the recommended HDMI display follow (these instructions)[http://wiki.sunfounder.cc/index.php?title=Raspberry_Pi_7%22_HD_1024*600_TFT_LCD_Screen_Display_Settings]

## Bumping up the volume
Run `alsamixer` select the headphones output and set it at 100% if you plan on using the audio out
