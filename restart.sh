#!/bin/sh
set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
echo "SCRIPT_DIR: $SCRIPT_DIR"

pids=$(ps | awk '/dbus_huaweisun2000_pvinverter/ {print $1}')

if [ -n "${pids}" ]; then
    echo "Found running process(es): $pids"
    for pid in $pids; do
        echo "Killing process: $pid"
        kill "$pid" 2>/dev/null || true
    done
else
    echo "No running dbus_huaweisun2000_pvinverter processes found."
fi

exit 0
