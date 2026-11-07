"""Require real simulator measurements from the running driver's D-Bus service."""

import math
import time

EXPECTED_POWER = {"/Ac/Power": 5800.0, "/Dc/Power": 6200.0}
PATHS = ("/Diagnostics/SuccessCount", "/Connected", *EXPECTED_POWER)


def validate_snapshot(snapshot):
    if snapshot.get("/Diagnostics/SuccessCount", 0) < 1:
        raise ValueError("No successful Modbus poll")
    if snapshot.get("/Connected") != 1:
        raise ValueError("Driver is disconnected")
    for path, expected in EXPECTED_POWER.items():
        try:
            matches = math.isclose(float(snapshot[path]), expected, abs_tol=0.1)
        except (KeyError, TypeError, ValueError):
            matches = False
        if not matches:
            raise ValueError(
                f"Unexpected simulator value for {path}: {snapshot.get(path)}"
            )


def main():
    import dbus

    bus = dbus.SystemBus()
    deadline = time.monotonic() + 60
    last_error = "Service not available"
    while time.monotonic() < deadline:
        try:
            snapshot = {}
            for path in PATHS:
                item = bus.get_object(
                    "com.victronenergy.pvinverter.sun2000", path, introspect=False
                )
                snapshot[path] = item.get_dbus_method(
                    "GetValue", "com.victronenergy.BusItem"
                )(timeout=2)
            validate_snapshot(snapshot)
        except (dbus.DBusException, ValueError) as error:
            last_error = str(error)
            time.sleep(0.5)
        else:
            print(f"Verified simulator telemetry: {snapshot}", flush=True)
            return
    raise SystemExit(f"Telemetry check timed out: {last_error}")


if __name__ == "__main__":
    main()
