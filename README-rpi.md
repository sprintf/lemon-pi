## Developing on Raspberry Pi

1. install python3.8

```sh
Follow instructions at (rpi-pyenv)[https://www.samwestby.com/tutorials/rpi-pyenv]
pyenv global 3.8.17
```

2. install gpsd, git etc

```sh
sudo apt-get install git gpsd gpsd-clients espeak
```

3. fetch the git repo

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

7. fix up numpy dependency to work on rpi (not sure if this is still needed)

```sh

sudo apt-get install libatlas-base-dev

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
