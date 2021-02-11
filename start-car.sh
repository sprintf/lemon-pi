#!/bin/bash
cd /home/pi/lemon-pi
. venv/bin/activate
./gen-protos.sh
python3 lemon_pi/car/main.py

