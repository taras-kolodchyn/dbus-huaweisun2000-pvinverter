#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SERVICE_NAME=$(basename $SCRIPT_DIR)
filename=/data/rc.local
rm /service/$SERVICE_NAME
# Kill python process running dbus-huaweisun2000-pvinverter.py
PID=$(ps | grep '[d]bus-huaweisun2000-pvinverter.py' | awk '{print $1}')
if [ -n "$PID" ]; then
  kill $PID
fi

# Kill multilog process for dbus-huaweisun2000
PID_LOG=$(ps | grep '[m]ultilog t s25000 n4 /var/log/dbus-huaweisun2000' | awk '{print $1}')
if [ -n "$PID_LOG" ]; then
  kill $PID_LOG
fi
chmod a-x $SCRIPT_DIR/service/run
$SCRIPT_DIR/restart.sh
STARTUP=$SCRIPT_DIR/install.sh
sed -i "\~$STARTUP~d" $filename
