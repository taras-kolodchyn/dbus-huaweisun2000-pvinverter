#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT=/workspace
INSTALL_ROOT=/data/dbus-huaweisun2000-pvinverter
USE_INSTALL_SH=${DBUS_HUAWEISUN2000_USE_INSTALL_SH:-0}

SIMULATION=${VENUS_SIMULATION:-a}
SIM_FLAGS=${VENUS_SIMULATION_FLAGS:---with-pvinverter}

SCRIPT_ROOT=/root

driver_root="$WORKSPACE_ROOT"
service_command=(python3 -m dbus_huaweisun2000_pvinverter)
settings_pythonpath=
original_qml_hash=
install_completed=0
SIM_PID=
qml_settings_file=/opt/victronenergy/gui/qml/PageSettingsFronius.qml

prepare_install_layout() {
  mkdir -p /opt/victronenergy/gui/qml
  if [ ! -f "$qml_settings_file" ]; then
    cat >"$qml_settings_file" <<'EOF'
MbPage {
    model: VisibleItemModel
}
EOF
  fi
}

prepare_venus_stubs() {
  if [ ! -e /service/start-gui ] && [ ! -x /usr/local/bin/svc ]; then
    cat >/usr/local/bin/svc <<'EOF'
#!/usr/bin/env bash
if [ "$#" -eq 2 ] && [ "$1" = "-t" ] && [ "$2" = "/service/start-gui" ] && [ ! -e /service/start-gui ]; then
  exit 0
fi

exec /usr/bin/svc "$@"
EOF
    chmod +x /usr/local/bin/svc
  fi
}

if [ "$USE_INSTALL_SH" = "1" ]; then
  rm -rf "$INSTALL_ROOT"
  mkdir -p /data
  prepare_install_layout
  prepare_venus_stubs
  cp -a "$WORKSPACE_ROOT/." "$INSTALL_ROOT"
  driver_root="$INSTALL_ROOT"
  service_command=("$INSTALL_ROOT/service/run")
  settings_pythonpath="$INSTALL_ROOT/src"
  original_qml_hash=$(sha256sum "$qml_settings_file" | awk '{print $1}')
fi

cd "$driver_root"

if [ -x "$SCRIPT_ROOT/start_services.sh" ]; then
  (cd "$SCRIPT_ROOT" && ./start_services.sh)
else
  echo "WARNING: start_services.sh not available; skipping service startup" >&2
fi

if [ -x "$SCRIPT_ROOT/simulate.sh" ]; then
  (cd "$SCRIPT_ROOT" && ./simulate.sh ${SIM_FLAGS} "${SIMULATION}") &
  SIM_PID=$!
else
  echo "WARNING: simulate.sh not available; skipping simulation playback" >&2
fi

cleanup() {
    if [ "$USE_INSTALL_SH" = "1" ] && [ "$install_completed" = "1" ] && [ -f "$driver_root/uninstall.sh" ]; then
        (cd "$driver_root" && bash uninstall.sh)
        restored_qml_hash=$(sha256sum "$qml_settings_file" | awk '{print $1}')
        test "$restored_qml_hash" = "$original_qml_hash"
        test ! -e /service/dbus-huaweisun2000-pvinverter
    fi

    if [ -n "$SIM_PID" ]; then
        kill "$SIM_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

python3 - <<'PY'
import time
import sys
for _ in range(30):
    try:
        import dbus  # noqa: F401
        dbus.SystemBus()
        break
    except Exception:
        time.sleep(1)
else:
    sys.exit("D-Bus system bus not available")
PY

python3 -m pip install -e "$WORKSPACE_ROOT"

if [ "$USE_INSTALL_SH" = "1" ]; then
  bash install.sh
  test -L /service/dbus-huaweisun2000-pvinverter
  test -f /opt/victronenergy/gui/qml/PageSettingsHuaweiSUN2000.qml
  grep -q "// dbus-huaweisun2000 start" "$qml_settings_file"
  install_completed=1
fi

PYTHONPATH="${settings_pythonpath}${PYTHONPATH:+:$PYTHONPATH}" python3 - <<PY
import os
from dbus.mainloop.glib import DBusGMainLoop
from dbus_huaweisun2000_pvinverter.settings import HuaweiSUN2000Settings

host = os.getenv("DBUS_HUAWEISUN2000_MODBUS_HOST")
port = os.getenv("DBUS_HUAWEISUN2000_MODBUS_PORT")
unit = os.getenv("DBUS_HUAWEISUN2000_MODBUS_UNIT")

if any([host, port, unit]):
    DBusGMainLoop(set_as_default=True)
    settings = HuaweiSUN2000Settings()
    if host:
        settings.set("modbus_host", host)
    if port:
        settings.set("modbus_port", int(port))
    if unit:
        settings.set("modbus_unit", int(unit))
PY

if [ "$USE_INSTALL_SH" = "1" ]; then
  "${service_command[@]}" >/tmp/dbus-huaweisun2000-service.log 2>&1
  grep -q "Connected to dbus" /tmp/dbus-huaweisun2000-service.log
  grep -q "Oneshot mode active" /tmp/dbus-huaweisun2000-service.log
else
  exec "${service_command[@]}"
fi
