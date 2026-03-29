#!/bin/bash
set -eu

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
SERVICE_NAME=$(basename "$SCRIPT_DIR")
RC_LOCAL="/data/rc.local"
GUI_V2_DIR="/opt/victronenergy/gui-v2"
BACKUP_DIR="$SCRIPT_DIR/.install-backup"
LEGACY_GUI_V2_BACKUP_DIR="$BACKUP_DIR/gui-v2"

stop_service() {
    local service_path=$1
    if [ ! -e "$service_path" ]; then
        return
    fi

    echo "INFO: Stopping service: $service_path"
    svc -d "$service_path/log" 2>/dev/null || true
    svc -d "$service_path" 2>/dev/null || true
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

    echo "INFO: Restoring legacy gui-v2 overlay backups from $backup_root"
    find "$backup_root" -type f -name '*.orig' | while read -r backup_path; do
        relative_path=${backup_path#"$backup_root"/}
        target_path="$target_root/${relative_path%.orig}"

        mkdir -p "$(dirname "$target_path")"
        echo "INFO: Restoring $target_path from $backup_path"
        cp "$backup_path" "$target_path"
        rm -f "$backup_path"
    done

    find "$backup_root" -depth -type d -empty -delete 2>/dev/null || true
    rmdir "$BACKUP_DIR" 2>/dev/null || true
}

echo "SCRIPT_DIR: $SCRIPT_DIR"
echo "SERVICE_NAME: $SERVICE_NAME"
stop_service "/service/$SERVICE_NAME"

if [ -L "/service/$SERVICE_NAME" ]; then
    EXISTING_TARGET=$(readlink "/service/$SERVICE_NAME" || true)
    if [ -n "$EXISTING_TARGET" ] && [ -d "$EXISTING_TARGET" ]; then
        echo "INFO: Cleaning stale supervise state in $EXISTING_TARGET"
        cleanup_supervise_dirs "$EXISTING_TARGET"
    fi
fi
cleanup_supervise_dirs "$SCRIPT_DIR/service"

chmod 744 "$SCRIPT_DIR/restart.sh" "$SCRIPT_DIR/uninstall.sh" "$SCRIPT_DIR/configure.sh"
chmod 755 "$SCRIPT_DIR/service/run" "$SCRIPT_DIR/service/log/run"

ln -sfn "$SCRIPT_DIR/service" "/service/$SERVICE_NAME"

if [ ! -f "$RC_LOCAL" ]; then
    touch "$RC_LOCAL"
    chmod 755 "$RC_LOCAL"
    echo "#!/bin/bash" >> "$RC_LOCAL"
    echo >> "$RC_LOCAL"
fi

grep -qxF "$SCRIPT_DIR/install.sh" "$RC_LOCAL" || echo "$SCRIPT_DIR/install.sh" >> "$RC_LOCAL"

restore_legacy_gui_v2_backups "$LEGACY_GUI_V2_BACKUP_DIR" "$GUI_V2_DIR"

svc -u "/service/$SERVICE_NAME/log" 2>/dev/null || true
svc -u "/service/$SERVICE_NAME" 2>/dev/null || true
