#!/bin/bash
set -eu

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
SERVICE_NAME=$(basename "$SCRIPT_DIR")
RC_LOCAL="/data/rc.local"
GUI_V2_DIR="/opt/victronenergy/gui-v2"
BACKUP_DIR="$SCRIPT_DIR/.install-backup"
LEGACY_GUI_V2_BACKUP_DIR="$BACKUP_DIR/gui-v2"
RC_LOCAL_ENTRY="sh $SCRIPT_DIR/install.sh"
LEGACY_RC_LOCAL_ENTRY="$SCRIPT_DIR/install.sh"

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

restore_legacy_gui_v2_backups() {
    local backup_root=$1
    local target_root=$2
    local backup_path
    local relative_path
    local target_path

    if [ ! -d "$backup_root" ] || [ ! -d "$target_root" ]; then
        return
    fi

    echo "Restoring legacy gui-v2 overlay backups from $backup_root"
    find "$backup_root" -type f -name '*.orig' | while read -r backup_path; do
        relative_path=${backup_path#"$backup_root"/}
        target_path="$target_root/${relative_path%.orig}"

        mkdir -p "$(dirname "$target_path")"
        echo "Restoring $target_path from $backup_path"
        cp "$backup_path" "$target_path"
        rm -f "$backup_path"
    done

    find "$backup_root" -depth -type d -empty -delete 2>/dev/null || true
    rmdir "$BACKUP_DIR" 2>/dev/null || true
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
    echo "Removing startup entries from $RC_LOCAL"
    sed -i "\~$RC_LOCAL_ENTRY~d" "$RC_LOCAL"
    sed -i "\~$LEGACY_RC_LOCAL_ENTRY~d" "$RC_LOCAL"
fi

restore_legacy_gui_v2_backups "$LEGACY_GUI_V2_BACKUP_DIR" "$GUI_V2_DIR"

echo "Uninstall script completed."
