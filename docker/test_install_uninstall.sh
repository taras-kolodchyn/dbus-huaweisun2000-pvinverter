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

cat >/usr/local/bin/dbus <<'"'"'EOF'"'"'
#!/bin/sh
printf "%s\n" "$*" >> /tmp/dbus.log
case "$4" in
  GetValue)
    case "$3" in
      /Settings/HuaweiSUN2000/ModbusHost) echo "'192.0.2.10'" ;;
      /Settings/HuaweiSUN2000/ModbusPort) echo "1502" ;;
      /Settings/HuaweiSUN2000/ModbusUnit) echo "3" ;;
      /Settings/HuaweiSUN2000/PhaseTypeOverride) echo "'three-phase'" ;;
      /Settings/HuaweiSUN2000/CustomName) echo "'Huawei Test'" ;;
      /Settings/HuaweiSUN2000/Position) echo "2" ;;
      /Settings/HuaweiSUN2000/UpdateTimeMS) echo "1000" ;;
      /Settings/HuaweiSUN2000/PowerCorrectionFactor) echo "1.0" ;;
      /Settings/Devices/HuaweiSUN2000/ClassAndVrmInstance) echo "'pvinverter:20'" ;;
      *) echo "0" ;;
    esac
    ;;
  SetValue)
    echo "0"
    ;;
  *)
    echo "0"
    ;;
esac
EOF
chmod +x /usr/local/bin/dbus

mkdir -p /service /data /var/log/dbus-huaweisun2000 /opt/victronenergy/gui-v2/Victron/VenusOS/data/common /opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar
printf "preserve-me\n" >/var/log/dbus-huaweisun2000/lock

cat >/opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml <<'"'"'EOF'"'"'
Device {
    readonly property real voltage: pvInverter.phases.singlePhaseVoltage
}
EOF

cat >/opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml <<'"'"'EOF'"'"'
Page {
    property string legacy: "original"
}
EOF

cp -a /repo/. /data/dbus-huaweisun2000-pvinverter
cd /data/dbus-huaweisun2000-pvinverter
mkdir -p service/supervise service/log/supervise
touch service/supervise/stale service/log/supervise/stale
mkdir -p .install-backup/gui-v2/Victron/VenusOS/data/common .install-backup/gui-v2/Victron/VenusOS/pages/solar
cp /opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml .install-backup/gui-v2/Victron/VenusOS/data/common/PvInverter.qml.orig
cp /opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml .install-backup/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml.orig
printf "patched\n" >/opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml
printf "patched\n" >/opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml

bash configure.sh --host 192.0.2.10 --port 1502 --unit 3 --position 2 --custom-name "Huawei Test" --phase-type three-phase --update-ms 1000 --power-correction 1.0 --vrm-instance 20 >/tmp/configure.log
grep -q "/Settings/HuaweiSUN2000/ModbusHost SetValue 192.0.2.10" /tmp/dbus.log
grep -q "/Settings/HuaweiSUN2000/ModbusPort SetValue 1502" /tmp/dbus.log
grep -q "/Settings/HuaweiSUN2000/ModbusUnit SetValue 3" /tmp/dbus.log
grep -q "/Settings/HuaweiSUN2000/Position SetValue 2" /tmp/dbus.log
grep -q "/Settings/HuaweiSUN2000/CustomName SetValue Huawei Test" /tmp/dbus.log
grep -q "/Settings/HuaweiSUN2000/PhaseTypeOverride SetValue three-phase" /tmp/dbus.log
grep -q "/Settings/HuaweiSUN2000/UpdateTimeMS SetValue 1000" /tmp/dbus.log
grep -q "/Settings/HuaweiSUN2000/PowerCorrectionFactor SetValue 1.0" /tmp/dbus.log
grep -q "/Settings/Devices/HuaweiSUN2000/ClassAndVrmInstance SetValue pvinverter:20" /tmp/dbus.log

bash install.sh

test -L /service/dbus-huaweisun2000-pvinverter
test "$(readlink /service/dbus-huaweisun2000-pvinverter)" = "/data/dbus-huaweisun2000-pvinverter/service"
grep -qxF "sh /data/dbus-huaweisun2000-pvinverter/install.sh" /data/rc.local
grep -qxF "preserve-me" /var/log/dbus-huaweisun2000/lock
grep -q "singlePhaseVoltage" /opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml
grep -q 'property string legacy: "original"' /opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml
test ! -e /data/dbus-huaweisun2000-pvinverter/.install-backup/gui-v2
test ! -e /data/dbus-huaweisun2000-pvinverter/service/supervise
test ! -e /data/dbus-huaweisun2000-pvinverter/service/log/supervise

chmod 644 /data/dbus-huaweisun2000-pvinverter/install.sh
rm -f /service/dbus-huaweisun2000-pvinverter
sh /data/rc.local
test -L /service/dbus-huaweisun2000-pvinverter
test "$(readlink /service/dbus-huaweisun2000-pvinverter)" = "/data/dbus-huaweisun2000-pvinverter/service"

: >/tmp/svc.log
bash uninstall.sh

test ! -e /service/dbus-huaweisun2000-pvinverter
! grep -q "/data/dbus-huaweisun2000-pvinverter/install.sh" /data/rc.local
grep -qxF "preserve-me" /var/log/dbus-huaweisun2000/lock
grep -q "singlePhaseVoltage" /opt/victronenergy/gui-v2/Victron/VenusOS/data/common/PvInverter.qml
grep -q 'property string legacy: "original"' /opt/victronenergy/gui-v2/Victron/VenusOS/pages/solar/SolarInputListPage.qml
'
