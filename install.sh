#!/bin/bash
set -eu

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
SERVICE_NAME=$(basename "$SCRIPT_DIR")
LOCK_FILE="/var/log/dbus-huaweisun2000/lock"
RC_LOCAL="/data/rc.local"
GUI_QML_DIR="/opt/victronenergy/gui/qml"
INVERTERS_SETTINGS_FILE="$GUI_QML_DIR/PageSettingsFronius.qml"
BACKUP_DIR="$SCRIPT_DIR/.install-backup"
BACKUP_FILE="$BACKUP_DIR/PageSettingsFronius.qml.orig"

echo "SCRIPT_DIR: $SCRIPT_DIR"
echo "SERVICE_NAME: $SERVICE_NAME"

if [ -f "$LOCK_FILE" ]; then
    echo "INFO: Found lock file: $LOCK_FILE"
    PID=$(fuser "$LOCK_FILE" 2>/dev/null || true)
    if [ -n "$PID" ]; then
        echo "INFO: Stopping process holding lock: $PID"
        kill $PID 2>/dev/null || true
        sleep 1
    fi
    echo "INFO: Removing lock file: $LOCK_FILE"
    rm -f "$LOCK_FILE"
fi

chmod 744 "$SCRIPT_DIR/restart.sh" "$SCRIPT_DIR/uninstall.sh"
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
if ! grep -q "dbus-huaweisun2000 start" "$INVERTERS_SETTINGS_FILE"; then
    echo "INFO: Saving original $INVERTERS_SETTINGS_FILE to $BACKUP_FILE"
    cp "$INVERTERS_SETTINGS_FILE" "$BACKUP_FILE"
fi

sed -i '/\/\/ dbus-huaweisun2000 start/,/\/\/ dbus-huaweisun2000 end/d' "$INVERTERS_SETTINGS_FILE"
echo "INFO: Inserting Huawei SUN2000 menu entry into $INVERTERS_SETTINGS_FILE"
sed -i "/model: VisibleItemModel/ r $SCRIPT_DIR/gui/menu_item.txt" "$INVERTERS_SETTINGS_FILE"

cp -av "$SCRIPT_DIR"/gui/*.qml "$GUI_QML_DIR/"

svc -t /service/start-gui
