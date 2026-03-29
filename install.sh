#!/bin/bash
set -eu

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
SERVICE_NAME=$(basename "$SCRIPT_DIR")
RC_LOCAL="/data/rc.local"
GUI_V2_DIR="/opt/victronenergy/gui-v2"
GUI_V2_OVERLAY_DIR="$SCRIPT_DIR/gui-v2"
BACKUP_DIR="$SCRIPT_DIR/.install-backup"

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

install_overlay_tree() {
    local source_root=$1
    local target_root=$2
    local backup_root=$3
    local source
    local relative_path
    local target_path
    local backup_path

    if [ ! -d "$source_root" ] || [ ! -d "$target_root" ]; then
        return
    fi

    find "$source_root" -type f | while read -r source; do
        relative_path=${source#"$source_root"/}
        target_path="$target_root/$relative_path"
        backup_path="$backup_root/$relative_path.orig"

        mkdir -p "$(dirname "$target_path")" "$(dirname "$backup_path")"
        if [ -f "$target_path" ] && [ ! -f "$backup_path" ]; then
            echo "INFO: Backing up $target_path to $backup_path"
            cp "$target_path" "$backup_path"
        fi
        echo "INFO: Installing overlay $source -> $target_path"
        cp "$source" "$target_path"
    done
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

mkdir -p "$BACKUP_DIR"
install_overlay_tree "$GUI_V2_OVERLAY_DIR" "$GUI_V2_DIR" "$BACKUP_DIR/gui-v2"

svc -u "/service/$SERVICE_NAME/log" 2>/dev/null || true
svc -u "/service/$SERVICE_NAME" 2>/dev/null || true

svc -t /service/start-gui
