#!/bin/bash
set -x
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SERVICE_NAME=$(basename $SCRIPT_DIR)
filename=/data/rc.local

echo "Removing service: /service/$SERVICE_NAME"
if rm /service/$SERVICE_NAME; then
  echo "Removed /service/$SERVICE_NAME successfully."
else
  echo "Failed to remove /service/$SERVICE_NAME. It might already be removed."
fi

echo "Killing python process running dbus_huaweisun2000_pvinverter"
PIDS=$(ps | grep '[d]bus_huaweisun2000_pvinverter' | awk '{print $1}')
echo "Found PIDs: $PIDS"
if [ -n "$PIDS" ]; then
  for PID in $PIDS; do
    echo "Processing PID: $PID"
    if [[ -n "$PID" && "$PID" =~ ^[0-9]+$ ]]; then
      echo "Killing process: $PID"
      if kill "$PID" 2>/dev/null; then
        echo "Killed process $PID successfully."
      else
        echo "Failed to kill process $PID."
      fi
    fi
  done
fi

echo "Killing multilog process for dbus-huaweisun2000"
PIDS_LOG=$(ps | grep '[m]ultilog t s25000 n4 /var/log/dbus-huaweisun2000' | awk '{print $1}')
echo "Found multilog PIDs: $PIDS_LOG"
if [ -n "$PIDS_LOG" ]; then
  for PID in $PIDS_LOG; do
    echo "Processing multilog PID: $PID"
    if [ -n "$PID" ] && [[ "$PID" =~ ^[0-9]+$ ]]; then
      if kill -0 "$PID" 2>/dev/null; then
        echo "Killing multilog process: $PID"
        if kill "$PID" 2>/dev/null; then
          echo "Killed multilog process $PID successfully."
        else
          echo "Failed to kill multilog process $PID."
        fi
      else
        echo "Skip dead PID: '$PID'"
      fi
    else
      echo "Skip invalid PID: '$PID'"
    fi
  done
fi

if [ -f "$SCRIPT_DIR/service/run" ]; then
  echo "Changing permissions: chmod a-x $SCRIPT_DIR/service/run"
  chmod a-x $SCRIPT_DIR/service/run
else
  echo "File $SCRIPT_DIR/service/run not found, skipping chmod."
fi

if [ -f "$SCRIPT_DIR/restart.sh" ]; then
  echo "Running restart script: $SCRIPT_DIR/restart.sh"
  $SCRIPT_DIR/restart.sh
else
  echo "File $SCRIPT_DIR/restart.sh not found, skipping restart script."
fi

STARTUP=$SCRIPT_DIR/install.sh
echo "Removing startup entry from $filename: $STARTUP"
sed -i "\~$STARTUP~d" $filename

echo "Uninstall script completed."
