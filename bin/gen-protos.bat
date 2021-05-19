
SET needs_building="0"

IF NOT EXIST "lemon_pi\shared\generated\" (
  MKDIR "lemon_pi\shared\generated"
  SET needs_building="1"
)

IF NOT EXIST "lemon_pi\shared\generated\messages_pb2.py" (
  SET needs_building="1"
)

REM if [ lemon_pi/shared/generated/messages_pb2.py -ot lemon_pi/shared/protos/messages.proto ] ; then
REM   needs_building=1
REM fi

if %needs_building% == "1" (
  protoc.exe --python_out="lemon_pi\shared\generated" ^
        -I="lemon_pi\shared\protos" ^
        messages.proto
) else (
  echo "no generation needed"
)
