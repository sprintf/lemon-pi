#!/bin/bash
cd /home/pi/lemon-pi
. venv/bin/activate
export PYTHONPATH=`pwd`
python3 car/main.py 2>> logs/lemon-pi.log

