#!/bin/bash

needs_building=0

if [ ! -d lemon_pi/shared/generated ] ; then
  mkdir lemon_pi/shared/generated
  needs_building=1
fi

if [ ! -f lemon_pi/shared/generated/messages_pb2.py ] ; then
  needs_building=1
fi

if [ lemon_pi/shared/generated/messages_pb2.py -ot lemon_pi/shared/protos/messages.proto ] ; then
  needs_building=1
fi

if [ ${needs_building} -eq 1 ] ; then
  protoc --python_out=lemon_pi/shared/generated \
        -I=lemon_pi/shared/protos \
        messages.proto
else
  echo "no generation needed"
fi
