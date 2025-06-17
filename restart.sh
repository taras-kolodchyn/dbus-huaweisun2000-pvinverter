#!/bin/bash
set -e
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"

PIDS=$(pgrep -f "python -u $SCRIPT_DIR/dbus-huaweisun2000-pvinverter.py")

if [ -n "$PIDS" ]; then
    echo "Found running process(es): $PIDS"
    for PID in $PIDS; do
        echo "Killing process: $PID"
        kill "$PID"
    done
else
    echo "No running dbus-huaweisun2000-pvinverter.py processes found."
fi
