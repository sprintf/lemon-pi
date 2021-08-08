#!/usr/bin/env bash

echo "setting up Raspberry Pi for Lemon Pi"

sudo apt-get update

#sudo apt-get install python3.8

sudo apt-get install git gpsd gpsd-clients
# needed for text to speech
sudo apt-get install espeak
# needed for pygame sounds
# may not be needed : we do need aplay for sure
# sudo apt-get install libsdl2-mixer-2.0.0

git clone https://github.com/sprintf/lemon-pi.git

cd lemon-pi

git clone https://github.com/sprintf/python-obd.git

python3 -m venv venv
. venv/bin/activate
pip3 install -e ./python-obd
pip3 install -r requirements-pi.txt

sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y protobuf-compiler

#turn off screen saver/blanking
xset dpms 0 0 0

echo "you need to disable screen saving"

cat <<EOM1 | sudo tee /etc/xdg/autostart/lemon-pi.desktop
[Desktop Entry]
Type=Application
Name=Lemon-Pi
Comment=Start Lemon-Pi OBD GPS Display
NoDisplay=False
Exec=/usr/bin/lxterminal -e /home/pi/lemon-pi/bin/start-car.sh
NotShowIn=GNOME;KDE;XFCE;
EOM1

cat <<EOM2 | sudo tee -a /boot/config.txt
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87

# uncomment to force a HDMI mode rather than DVI. This can make audio work in
# DMT (computer monitor) modes
hdmi_drive=2

hdmi_cvt=1024 576 60 3 0 0 0
EOM2

