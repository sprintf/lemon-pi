## Developing on Raspberry Pi

1. install python3

```sh
sudo apt-get install python3
```

2. install gpsd, git etc

```sh
sudo apt-get install git gpsd gpsd-clients
```

3. fetch the git repo

```sh
git clone https://github.com/sprintf/lemon-pi.git
```

4. cd into the lemon-pi directory

```sh
cd lemon-pi
```

5. [optional, depending on your obd device]

```sh
git clone https://github.com/sprintf/python-obd.git
```

6. setup venv

```sh
python3 -m venv venv
. venv/bin/activate
pip3 install -e ./python-obd/
pip3 install -r requirements.txt
```

7. fix up numpy dependency to work on rpi

```sh
sudo apt-get install libatlas-base-dev
```

8. Install protobuf 

```sh
sudo apt-get install protobuf-compiler
```

8. launch the lemon-pi application

```sh
./start-car.sh
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
Exec=/usr/bin/lxterminal -e /home/pi/lemon-pi/start.sh
NotShowIn=GNOME;KDE;XFCE;
```
