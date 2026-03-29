#!/bin/sh
set -eu

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SERVICE_NAME=$(basename "$SCRIPT_DIR")
SERVICE_PATH="/service/$SERVICE_NAME"
echo "SCRIPT_DIR: $SCRIPT_DIR"

if [ -e "$SERVICE_PATH" ]; then
    echo "Restarting supervised service: $SERVICE_PATH"
    svc -t "$SERVICE_PATH/log" 2>/dev/null || true
    svc -t "$SERVICE_PATH" 2>/dev/null || svc -u "$SERVICE_PATH" 2>/dev/null || true
    exit 0
fi

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
