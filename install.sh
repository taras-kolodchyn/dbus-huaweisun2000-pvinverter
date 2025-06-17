#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Handle lock file for log directory (prevents installer hangs)
LOCK_FILE="/var/log/dbus-huaweisun2000/lock"
if [ -f "$LOCK_FILE" ]; then
    echo "INFO: Found lock file: $LOCK_FILE"
    PID=$(fuser "$LOCK_FILE" 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "INFO: Killing process holding lock: $PID"
        kill -9 $PID
        sleep 1
    fi
    echo "INFO: Removing lock file: $LOCK_FILE"
    rm -f "$LOCK_FILE"
fi
echo "SCRIPT_DIR: $SCRIPT_DIR"
SERVICE_NAME=$(basename $SCRIPT_DIR)
echo "SERVICE_NAME: $SERVICE_NAME"
# set permissions for script files
chmod a+x $SCRIPT_DIR/restart.sh
chmod 744 $SCRIPT_DIR/restart.sh

chmod a+x $SCRIPT_DIR/uninstall.sh
chmod 744 $SCRIPT_DIR/uninstall.sh

chmod a+x $SCRIPT_DIR/service/run
chmod 755 $SCRIPT_DIR/service/run

chmod a+x $SCRIPT_DIR/service/log/run

# create sym-link to run script in deamon
ln -sfn $SCRIPT_DIR/service /service/$SERVICE_NAME

# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f $filename ]
then
    touch $filename
    chmod 755 $filename
    echo "#!/bin/bash" >> $filename
    echo >> $filename
fi

grep -qxF "$SCRIPT_DIR/install.sh" $filename || echo "$SCRIPT_DIR/install.sh" >> $filename

# The "PV inverters" page in Settings is somewhat specific for Fronius. Let's change that.
invertersSettingsFile="/opt/victronenergy/gui/qml/PageSettingsFronius.qml"

# Backup the original PageSettingsFronius.qml file with a timestamp before modification
backupFile="${invertersSettingsFile}_backup_$(date +%Y%m%d%H%M%S)"
echo "INFO: Creating backup of $invertersSettingsFile at $backupFile"
cp "$invertersSettingsFile" "$backupFile"

# Remove all old HuaweiSUN2000 related blocks including their surrounding braces.
# This removes any block containing 'menuHuaweiSUN2000', 'PageSettingsHuaweiSUN2000', or any line containing 'HuaweiSUN2000'.
echo "INFO: Removing old HuaweiSUN2000 related blocks from $invertersSettingsFile"
sed -i -e '/menuHuaweiSUN2000/,/}/d' \
       -e '/PageSettingsHuaweiSUN2000/,/}/d' \
       -e '/HuaweiSUN2000/,/}/d' "$invertersSettingsFile"

# Add new HuaweiSUN2000 menu entry only if it is not already present
if ! grep -q "PageSettingsHuaweiSUN2000" "$invertersSettingsFile"; then
    echo "INFO: Adding HuaweiSUN2000 menu entry to $invertersSettingsFile"
    sed -i "/model: VisibleItemModel/ r $SCRIPT_DIR/gui/menu_item.txt" "$invertersSettingsFile"
else
    echo "INFO: HuaweiSUN2000 menu already present in $invertersSettingsFile -- skipping modification"
fi

cp -av $SCRIPT_DIR/gui/*.qml /opt/victronenergy/gui/qml/

# As we've modified the GUI, we need to restart it
svc -t /service/start-gui