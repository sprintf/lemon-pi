#!/bin/bash

cd ~/lemon-pi
git pull
. venv/bin/activate
pip install -r requirements.txt

./bin/start-car.sh