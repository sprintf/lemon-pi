#!/bin/bash

needs_building=0

if [ ! -d shared/generated ] ; then
  mkdir shared/generated
  needs_building=1
fi

if [ ! -f shared/generated/messages_pb2.py ] ; then
  needs_building=1
fi

if [ shared/generated/messages_pb2.py -ot shared/protos/messages.proto ] ; then
  needs_building=1
fi

if [ ${needs_building} -eq 1 ] ; then
  protoc --python_out=shared/generated \
        -I=shared/protos \
        messages.proto
else
  echo "no generation needed"
fi
