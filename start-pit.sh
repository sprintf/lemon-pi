#!/bin/bash
. venv/bin/activate
export PYTHONPATH=`pwd`
./gen-protos.sh
python3 pit/main.py 2>> logs/lemon-pit.log

