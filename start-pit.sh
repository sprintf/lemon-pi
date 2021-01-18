#!/bin/bash
. venv/bin/activate
export PYTHONPATH=`pwd`
python3 pit/main.py 2>> logs/lemon-pit.log

