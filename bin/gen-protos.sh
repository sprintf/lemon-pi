#!/bin/bash

needs_building=0

package_dir="./"
proto_dir="./lemon_pi/protos"

if [ ! -d ${package_dir} ] ; then
  mkdir ${package_dir}
  needs_building=1
fi

# force ... temporary fix
rm ${package_dir}/*pb2*.py

if [ ! -f ${package_dir}/lemon_pi_pb2.py ] ; then
  needs_building=1
fi

if [ ! -f ${package_dir}/lemon_pi_pb2_grpc.py ] ; then
  needs_building=1
fi

if [ ${package_dir}/lemon_pi_pb2.py -ot ${proto_dir}/lemon-pi.proto ] ; then
  needs_building=1
fi

if [ ${package_dir}/lemon_pi_pb2_grpc.py -ot ${proto_dir}/lemon-pi.proto ] ; then
  needs_building=1
fi

if [ ${needs_building} -eq 1 ] ; then
  python -m grpc_tools.protoc \
        --python_out=${package_dir} \
        --grpc_python_out=${package_dir} \
        -I=lemon_pi/shared/protos \
        lemon-pi.proto race-flag-status.proto
else
  echo "no generation needed"
fi
