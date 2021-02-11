#!/bin/bash
. venv/bin/activate
export PYTHONPATH=`pwd`
./gen-protos.sh
python3 lemon_pi/pit/main.py

