#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"

PIDS=$(ps aux | grep "[d]bus-huaweisun2000-pvinverter.py" | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "Found running process(es): $PIDS"
    for PID in $PIDS; do
        echo "Killing process: $PID"
        kill "$PID"
    done
else
    echo "No running dbus-huaweisun2000-pvinverter.py processes found."
fi
# Restart script compatible with BusyBox (Venus OS)
# Kills all running dbus-huaweisun2000-pvinverter.py processes
#!/bin/sh
SCRIPT_DIR=$( cd -- "$( dirname -- "$0" )" && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"

PIDS=$(ps | grep '[d]bus-huaweisun2000-pvinverter.py' | awk '{print $1}')

if [ -n "$PIDS" ]; then
    echo "Found running process(es): $PIDS"
    for PID in $PIDS; do
        echo "Killing process: $PID"
        kill "$PID"
    done
else
    echo "No running dbus-huaweisun2000-pvinverter.py processes found."
fi