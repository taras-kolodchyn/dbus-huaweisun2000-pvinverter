#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
IMAGE=${INSTALL_SCRIPT_TEST_IMAGE:-debian:bookworm-slim}

docker run --rm \
    -v "$REPO_ROOT":/repo:ro \
    "$IMAGE" \
    bash -lc '
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update >/dev/null
apt-get install -y bash coreutils findutils grep procps psmisc sed >/dev/null

cat >/usr/local/bin/svc <<'"'"'EOF'"'"'
#!/bin/sh
printf "%s\n" "$*" >> /tmp/svc.log
exit 0
EOF
chmod +x /usr/local/bin/svc

mkdir -p /service /data /opt/victronenergy/gui/qml /opt/victronenergy/gui-v2/Victron/VenusOS/data/common /opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar /var/log/dbus-huaweisun2000
touch /service/start-gui
printf "preserve-me\n" >/var/log/dbus-huaweisun2000/lock

cat >/opt/victronenergy/gui/qml/PageSettingsFronius.qml <<'"'"'EOF'"'"'
MbPage {
    model: VisibleItemModel
}
EOF

cat >/opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml <<'"'"'EOF'"'"'
Device {
    readonly property real current: pvInverter.phases.singlePhaseCurrent
    readonly property real voltage: pvInverter.phases.singlePhaseVoltage
}
EOF

cat >/opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml <<'"'"'EOF'"'"'
Page {
    GradientListView {
        delegate: ListQuantityGroupNavigation {
            quantityModel: QuantityObjectModel {
                QuantityObject { object: solarInputDelegate; key: "voltage" }
                QuantityObject { object: solarInputDelegate; key: "current" }
            }
        }
    }
}
EOF

cp -a /repo/. /data/dbus-huaweisun2000-pvinverter
cd /data/dbus-huaweisun2000-pvinverter
mkdir -p service/supervise service/log/supervise
touch service/supervise/stale service/log/supervise/stale

original_hash=$(sha256sum /opt/victronenergy/gui/qml/PageSettingsFronius.qml | awk "{print \$1}")
original_gui_v2_pvinverter_hash=$(sha256sum /opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml | awk "{print \$1}")
original_gui_v2_solar_list_hash=$(sha256sum /opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml | awk "{print \$1}")

bash install.sh

test -L /service/dbus-huaweisun2000-pvinverter
test "$(readlink /service/dbus-huaweisun2000-pvinverter)" = "/data/dbus-huaweisun2000-pvinverter/service"
grep -qxF "/data/dbus-huaweisun2000-pvinverter/install.sh" /data/rc.local
grep -q "// dbus-huaweisun2000 start" /opt/victronenergy/gui/qml/PageSettingsFronius.qml
test -f /opt/victronenergy/gui/qml/PageSettingsHuaweiSUN2000.qml
test -f /data/dbus-huaweisun2000-pvinverter/.install-backup/PageSettingsFronius.qml.orig
test -f /data/dbus-huaweisun2000-pvinverter/.install-backup/gui-v2/Victron/VenusOS/data/common/PvInverter.qml.orig
test -f /data/dbus-huaweisun2000-pvinverter/.install-backup/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml.orig
grep -q "_acVoltage" /opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml
grep -q "displayVoltage" /opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml
grep -qxF "preserve-me" /var/log/dbus-huaweisun2000/lock
test ! -e /data/dbus-huaweisun2000-pvinverter/service/supervise
test ! -e /data/dbus-huaweisun2000-pvinverter/service/log/supervise
grep -q -- "-t /service/start-gui" /tmp/svc.log

modified_hash=$(sha256sum /opt/victronenergy/gui/qml/PageSettingsFronius.qml | awk "{print \$1}")
test "$modified_hash" != "$original_hash"

: >/tmp/svc.log
bash uninstall.sh

test ! -e /service/dbus-huaweisun2000-pvinverter
! grep -q "/data/dbus-huaweisun2000-pvinverter/install.sh" /data/rc.local
test ! -f /opt/victronenergy/gui/qml/PageSettingsHuaweiSUN2000.qml
grep -qxF "preserve-me" /var/log/dbus-huaweisun2000/lock
restored_hash=$(sha256sum /opt/victronenergy/gui/qml/PageSettingsFronius.qml | awk "{print \$1}")
test "$restored_hash" = "$original_hash"
restored_gui_v2_pvinverter_hash=$(sha256sum /opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml | awk "{print \$1}")
restored_gui_v2_solar_list_hash=$(sha256sum /opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml | awk "{print \$1}")
test "$restored_gui_v2_pvinverter_hash" = "$original_gui_v2_pvinverter_hash"
test "$restored_gui_v2_solar_list_hash" = "$original_gui_v2_solar_list_hash"
grep -q -- "-t /service/start-gui" /tmp/svc.log
'
