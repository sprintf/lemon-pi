## Developing on Raspberry Pi

1. install python3

sudo apt-get install python3

2. install gpsd, git etc

sudo apt-get install git gpsd gpsd-clients

3. fetch the git repo

git clone https://github.com/sprintf/lemon-pi.git

4. cd into the lemon-pi directory

cd lemon-pi

5. [optional, depending on your obd device]

git clone https://github.com/brendan-w/python-obd.git

6. setup venv

python3 -m venv venv
. venv/bin/activate
pip3 install -e ./python-obd/
pip3 install -r requirements.txt

7. fix up numpy dependency to work on rpi

sudo apt-get install libatlas-base-dev

8. launch the lemon-pi application

python3 main.py



