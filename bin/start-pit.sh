#!/bin/bash
. venv/bin/activate
export PYTHONPATH=`pwd`
bin/gen-protos.sh
python lemon_pi/pit/lemon-pi-pit.py

