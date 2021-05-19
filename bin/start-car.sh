#!/bin/bash
cd /home/pi/lemon-pi
. venv/bin/activate
export PYTHONPATH=`pwd`
bin/gen-protos.sh
python lemon_pi/car/main.py

