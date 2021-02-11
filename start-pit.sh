#!/bin/bash
. venv/bin/activate
./gen-protos.sh
python3 lemon_pi/pit/main.py

