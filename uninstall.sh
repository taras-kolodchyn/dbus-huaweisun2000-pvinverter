#!/bin/bash
set -eu

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
SERVICE_NAME=$(basename "$SCRIPT_DIR")
RC_LOCAL="/data/rc.local"
GUI_V2_DIR="/opt/victronenergy/gui-v2"
GUI_V2_OVERLAY_DIR="$SCRIPT_DIR/gui-v2"
BACKUP_DIR="$SCRIPT_DIR/.install-backup"

stop_supervised_service() {
    local service_path=$1
    if [ ! -e "$service_path" ]; then
        return
    fi

    echo "Stopping supervised service: $service_path"
    svc -dx "$service_path/log" 2>/dev/null || true
    svc -dx "$service_path" 2>/dev/null || true
    sleep 1
}

cleanup_supervise_dirs() {
    local service_root=$1
    rm -rf "$service_root/supervise" "$service_root/log/supervise"
}

restore_overlay_tree() {
    local source_root=$1
    local target_root=$2
    local backup_root=$3
    local source
    local relative_path
    local target_path
    local backup_path

    if [ ! -d "$source_root" ]; then
        return
    fi

    find "$source_root" -type f | while read -r source; do
        relative_path=${source#"$source_root"/}
        target_path="$target_root/$relative_path"
        backup_path="$backup_root/$relative_path.orig"

        if [ -f "$backup_path" ]; then
            echo "Restoring $target_path from $backup_path"
            cp "$backup_path" "$target_path"
            rm -f "$backup_path"
        else
            rm -f "$target_path"
        fi
    done
}

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

stop_supervised_service "/service/$SERVICE_NAME"
cleanup_supervise_dirs "$SCRIPT_DIR/service"

echo "Removing service: /service/$SERVICE_NAME"
rm -f "/service/$SERVICE_NAME"

stop_matching_processes "driver" "[d]bus_huaweisun2000_pvinverter"
stop_matching_processes "multilog" "[m]ultilog t s25000 n4 /var/log/dbus-huaweisun2000"

if [ -f "$RC_LOCAL" ]; then
    STARTUP=$SCRIPT_DIR/install.sh
    echo "Removing startup entry from $RC_LOCAL: $STARTUP"
    sed -i "\~$STARTUP~d" "$RC_LOCAL"
fi

restore_overlay_tree "$GUI_V2_OVERLAY_DIR" "$GUI_V2_DIR" "$BACKUP_DIR/gui-v2"
find "$BACKUP_DIR/gui-v2" -depth -type d -empty -delete 2>/dev/null || true
rmdir "$BACKUP_DIR" 2>/dev/null || true

if [ -e /service/start-gui ]; then
    svc -t /service/start-gui || true
fi

echo "Uninstall script completed."
