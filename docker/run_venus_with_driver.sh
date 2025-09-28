#!/usr/bin/env bash
set -euo pipefail

cd /workspace

SIMULATION=${VENUS_SIMULATION:-a}
SIM_FLAGS=${VENUS_SIMULATION_FLAGS:---with-pvinverter}

SCRIPT_ROOT=/root

if [ -x "$SCRIPT_ROOT/start_services.sh" ]; then
  (cd "$SCRIPT_ROOT" && ./start_services.sh)
else
  echo "WARNING: start_services.sh not available; skipping service startup" >&2
fi

if [ -x "$SCRIPT_ROOT/simulate.sh" ]; then
  (cd "$SCRIPT_ROOT" && ./simulate.sh ${SIM_FLAGS} "${SIMULATION}") &
  SIM_PID=$!
  cleanup() {
      kill "$SIM_PID" 2>/dev/null || true
  }
  trap cleanup EXIT
else
  echo "WARNING: simulate.sh not available; skipping simulation playback" >&2
fi

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

python3 -m pip install -e .

python3 - <<PY
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

exec python3 -m dbus_huaweisun2000_pvinverter
