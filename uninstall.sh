#!/bin/bash
set -eu

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
SERVICE_NAME=$(basename "$SCRIPT_DIR")
RC_LOCAL="/data/rc.local"
GUI_QML_DIR="/opt/victronenergy/gui/qml"
INVERTERS_SETTINGS_FILE="$GUI_QML_DIR/PageSettingsFronius.qml"
CUSTOM_SETTINGS_FILE="$GUI_QML_DIR/PageSettingsHuaweiSUN2000.qml"
BACKUP_DIR="$SCRIPT_DIR/.install-backup"
BACKUP_FILE="$BACKUP_DIR/PageSettingsFronius.qml.orig"

stop_matching_processes() {
    local label=$1
    local pattern=$2
    local pids

    pids=$(ps | grep "$pattern" | awk '{print $1}' || true)
    if [ -z "$pids" ]; then
        echo "No running ${label} processes found."
        return
    fi

    echo "Stopping ${label} process(es): $pids"
    for pid in $pids; do
        case "$pid" in
            ''|*[!0-9]*)
                echo "Skip invalid PID: '$pid'"
                ;;
            *)
                kill "$pid" 2>/dev/null || true
                ;;
        esac
    done
}

echo "Removing service: /service/$SERVICE_NAME"
rm -f "/service/$SERVICE_NAME"

stop_matching_processes "driver" "[d]bus_huaweisun2000_pvinverter"
stop_matching_processes "multilog" "[m]ultilog t s25000 n4 /var/log/dbus-huaweisun2000"

if [ -f "$RC_LOCAL" ]; then
    STARTUP=$SCRIPT_DIR/install.sh
    echo "Removing startup entry from $RC_LOCAL: $STARTUP"
    sed -i "\~$STARTUP~d" "$RC_LOCAL"
fi

if [ -f "$BACKUP_FILE" ]; then
    echo "Restoring $INVERTERS_SETTINGS_FILE from backup"
    cp "$BACKUP_FILE" "$INVERTERS_SETTINGS_FILE"
    rm -f "$BACKUP_FILE"
    rmdir "$BACKUP_DIR" 2>/dev/null || true
else
    sed -i '/\/\/ dbus-huaweisun2000 start/,/\/\/ dbus-huaweisun2000 end/d' "$INVERTERS_SETTINGS_FILE"
fi

rm -f "$CUSTOM_SETTINGS_FILE"

if [ -e /service/start-gui ]; then
    svc -t /service/start-gui || true
fi

echo "Uninstall script completed."
