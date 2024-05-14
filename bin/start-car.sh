#!/bin/bash
cd /home/pi/lemon-pi
. venv/bin/activate
if `grep -q GPSCTL_ARGS lemon_pi/config/local_settings_car.py` ; then
  echo "found custom GPSCTL_ARGS"
  gps_ctl=`grep GPSCTL_ARGS lemon_pi/config/local_settings_car.py`
  gps_args=`echo $gps_ctl | sed -e 's/"//g' -e 's/=//' -e 's/GPSCTL_ARGS//'`
  if ( gpsctl $gps_args ); then
    echo "gpsctl configured"
  else
    sleep 1
    if ( gpsctl $gps_args ); then
      echo "gpsctl configured on second attempt"
    else
      echo "gps not configured, exiting"
      exit 1
    fi
  fi
fi
export PYTHONPATH=`pwd`
python lemon_pi/car/main.py

