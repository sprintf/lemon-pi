#!/bin/bash
cd /home/pi/lemon-pi
. venv/bin/activate
python3 main.py 2>> logs/lemon-pi.log

