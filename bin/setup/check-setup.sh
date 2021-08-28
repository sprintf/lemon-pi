#!/usr/bin/env bash

check_for() {
  if ! command -v $1 &> /dev/null
  then
    echo "$1 is not installed"
    exit
  fi
}

check_for "gpsd"
check_for "espeak"
check_for "protoc"
check_for "aplay"
check_for "alsamixer"

if [ ! -d /var/lib/lemon-pi ];
then
  echo "no lemon pi track directory"
  exit
fi

if [ ! -d /home/pi/lemon-pi ];
then
  echo "no lemon pi installed"
  exit
fi

if [ ! -f /etc/xdg/autostart/lemon-pi.desktop ];
then
  echo "no autostart for lemon pi"
  exit
fi


# check the screen saver is disabled
if ! ( xset q | grep -A 2 Screen | grep -q "timeout:  0" )
then
  echo "screen saver not disabled"
  exit
fi

# check other display options
check_boot_config() {
  if ! grep -q -e "^$1" /boot/config.txt
  then
    echo "$1 missing from /boot/config.txt"
    exit
  fi
}

check_boot_config "hdmi_force_hotplug=1"
check_boot_config "hdmi_group=2"
check_boot_config "hdmi_mode=87"
check_boot_config "hdmi_drive=2"
check_boot_config "hdmi_cvt=1024 576 60 3 0 0 0"







