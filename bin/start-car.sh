#!/bin/bash
cd /home/pi/lemon-pi
. venv/bin/activate
export PYTHONPATH=`pwd`
python lemon_pi/car/main.py

