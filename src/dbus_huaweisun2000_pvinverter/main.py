#!/usr/bin/env python3

"""
A class to put a simple service on the dbus, according to victron standards, with
constantly updating paths. See example usage below. It is used to generate dummy data
for other processes that rely on the dbus. See files in dbus_vebus_to_pvinverter/test
and dbus_vrm/test for other usage examples.

To change a value while testing, without stopping your dummy script and changing its
initial value, write to the dummy data via the dbus. See example.

https://github.com/victronenergy/dbus_vebus_to_pvinverter/tree/master/test
"""

import logging
import os
import platform
import sys
import time
from typing import Dict, Optional

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

from .connector_modbus import ModbusDataCollector2000Delux
from .metrics import SERVICE_METRICS
from .settings import HuaweiSUN2000Settings
from . import config

try:  # Prefer the environment-provided vedbus, but fall back to Venus OS path.
    from vedbus import VeDbusService
except ModuleNotFoundError:  # pragma: no cover - exercised only on target hardware
    sys.path.insert(
        1,
        os.path.join(
            os.path.dirname(__file__),
            "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python",
        ),
    )
    try:
        from vedbus import VeDbusService
    except ModuleNotFoundError as err:  # pragma: no cover - indicates misconfigured env
        raise RuntimeError(
            "Unable to import vedbus. Ensure velib_python is available on PYTHONPATH."
        ) from err

LOG = logging.getLogger(__name__)


class _RuntimeNoiseFilter(logging.Filter):
    NOISY_MESSAGES = {"start update", "end update"}
    NOISY_PREFIXES = ("set /",)

    def filter(self, record):
        message = record.getMessage()
        if record.name == "root" and (
            message in self.NOISY_MESSAGES
            or any(message.startswith(prefix) for prefix in self.NOISY_PREFIXES)
        ):
            return False
        return True


def _is_missing_static_metadata(value):
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip().lower() in {"", "unknown", "x", "none"}

    return False


def _normalize_product_id(model_id):
    try:
        product_id = int(float(model_id))
    except (TypeError, ValueError):
        return 0

    return product_id if product_id > 0 else 0


def _normalize_hardware_version(hardware_version, partnumber):
    if _is_missing_static_metadata(hardware_version):
        if not _is_missing_static_metadata(partnumber):
            return partnumber
    return hardware_version


class DbusSun2000Service:
    def __init__(
        self,
        servicename,
        settings,
        paths,
        data_connector,
        serialnumber="X",
        partnumber="X",
        productname="Huawei Sun2000 PV-Inverter",
        firmware_version="1.0",
        software_version="",
        hardware_version="0",
        model_id=0,
        phase_type="Unknown",
        *,
        service_factory=VeDbusService,
        timeout_add=GLib.timeout_add,
    ):
        self._dbusservice = service_factory(servicename, register=False)
        self._settings = settings
        self._paths = paths
        self._data_connector = data_connector
        self._service_name = servicename
        self._update_interval_ms = max(int(settings.get("update_time_ms")), 100)
        self._timeout_add = timeout_add
        self._failure_count = 0
        self._last_update: Optional[float] = None

        logging.debug(
            "%s /DeviceInstance = %d" % (servicename, settings.get_vrm_instance())
        )

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion",
            "Unknown version, and running on Python " + platform.python_version(),
        )
        self._dbusservice.add_path("/Mgmt/Connection", "Internal Modbus TCP/UDP")

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", settings.get_vrm_instance())
        self._dbusservice.add_path("/ProductId", _normalize_product_id(model_id))
        self._dbusservice.add_path("/ModelID", model_id)
        self._dbusservice.add_path("/ProductName", productname)
        self._dbusservice.add_path(
            "/CustomName",
            settings.get("custom_name"),
            writeable=True,
            onchangecallback=self._handlechangedvalue,
        )
        self._dbusservice.add_path("/FirmwareVersion", firmware_version)
        self._dbusservice.add_path("/Info/SoftwareVersion", software_version)
        self._dbusservice.add_path(
            "/HardwareVersion",
            _normalize_hardware_version(hardware_version, partnumber),
        )
        self._dbusservice.add_path("/Info/PhaseType", phase_type)
        self._dbusservice.add_path("/Connected", 1, writeable=True)

        # Create the mandatory objects
        self._dbusservice.add_path("/Latency", None)
        self._dbusservice.add_path("/Role", "pvinverter")
        self._dbusservice.add_path(
            "/Position",
            settings.get("position"),
            writeable=True,
            onchangecallback=self._handlechangedvalue,
        )  # 0 = AC Input, 1 = AC-Out 1, AC-Out 2
        self._dbusservice.add_path("/Serial", serialnumber)
        self._dbusservice.add_path("/Part", partnumber)
        self._dbusservice.add_path("/ErrorCode", 0)
        self._dbusservice.add_path("/UpdateIndex", 0)
        # set path StatusCode to 7=Running so VRM detects a working PV-Inverter
        self._dbusservice.add_path("/StatusCode", 7)

        for _path, _settings in paths.items():
            self._dbusservice.add_path(
                _path,
                _settings["initial"],
                gettextcallback=_settings.get("textformat", lambda p, v: v),
                writeable=True,
                onchangecallback=self._handlechangedvalue,
            )

        self._dbusservice.register()

        self._schedule_next_update(self._update_interval_ms)

    def _schedule_next_update(self, delay_ms):
        self._timeout_add(max(int(delay_ms), 100), self._update)

    def _update(self):
        start = time.monotonic()
        next_delay_ms = self._update_interval_ms
        with self._dbusservice as s:

            try:
                meter_data: Optional[Dict[str, object]] = self._data_connector.getData()

                if meter_data is None:
                    raise RuntimeError("Modbus returned no data")

                updated_paths = 0
                for path, value in meter_data.items():
                    if path not in s:
                        LOG.debug("Ignoring unexpected datapoint %s", path)
                        continue
                    s[path] = value
                    updated_paths += 1

                # increment UpdateIndex - to show that new data is available (and wrap)
                s["/UpdateIndex"] = (s["/UpdateIndex"] + 1) % 256

                # update lastupdate vars
                self._last_update = time.time()
                latency_ms = round((time.monotonic() - start) * 1000, 1)
                s["/Latency"] = latency_ms
                s["/Connected"] = 1
                status_message = meter_data.get("status_message")
                if status_message:
                    s["/Status"] = status_message
                else:
                    try:
                        if s["/Status"]:
                            s["/Status"] = ""
                    except KeyError:
                        pass

                if self._failure_count > 0:
                    LOG.info(
                        (
                            "Recovered %s after %d failed update(s); applied "
                            "%d datapoints in %.1fms"
                        ),
                        self._service_name,
                        self._failure_count,
                        updated_paths,
                        latency_ms,
                    )
                else:
                    LOG.debug(
                        "Updated %s with %d datapoints in %.1fms",
                        self._service_name,
                        updated_paths,
                        latency_ms,
                    )

                self._failure_count = 0

            except Exception as e:
                self._failure_count += 1
                backoff_seconds = min(
                    (self._update_interval_ms / 1000.0)
                    * (2 ** (self._failure_count - 1)),
                    60,
                )
                next_delay_ms = int(backoff_seconds * 1000)
                s["/Connected"] = 0
                s["/Status"] = f"Update failed: {e}"[:80]
                LOG.warning(
                    "Update failed for %s (failure #%d, retry in %.1fs): %s",
                    self._service_name,
                    self._failure_count,
                    backoff_seconds,
                    e,
                )
                LOG.debug("Update traceback for %s", self._service_name, exc_info=e)

        self._schedule_next_update(next_delay_ms)
        return False

    def _handlechangedvalue(self, path, value):
        if path == "/Position":
            try:
                position = int(value)
            except (TypeError, ValueError):
                LOG.warning("Rejecting invalid position value: %r", value)
                return False

            if position < 0 or position > 2:
                LOG.warning("Rejecting out-of-range position value: %r", value)
                return False

            self._settings.set("position", position)
            LOG.info("Updated runtime position to %d", position)
            return True

        if path == "/CustomName":
            custom_name = str(value)
            self._settings.set("custom_name", custom_name)
            LOG.info("Updated runtime custom name to %s", custom_name)
            return True

        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change


def exit_mainloop(mainloop):
    mainloop.quit()


def _format_kwh(p, v):
    if v is None:
        return None
    return str(round(v, 2)) + " kWh"


def _format_wh(p, v):
    if v is None:
        return None
    return str(round(v, 1)) + " Wh"


def _format_a(p, v):
    if v is None:
        return None
    return str(round(v, 1)) + " A"


def _format_w(p, v):
    if v is None:
        return None
    return str(round(v, 1)) + " W"


def _format_v(p, v):
    if v is None:
        return None
    return str(round(v, 1)) + " V"


def _format_hz(p, v):
    if v is None:
        return None
    return f"{v:.4f}Hz"


def _format_n(p, v):
    if isinstance(v, int):
        return f"{v:d}"
    return str(v)


FORMATTERS = {
    "a": _format_a,
    "hz": _format_hz,
    "kwh": _format_kwh,
    "n": _format_n,
    "v": _format_v,
    "w": _format_w,
    "wh": _format_wh,
}


def _build_dbus_paths():
    paths = {}
    for path, spec in SERVICE_METRICS.items():
        path_spec = {"initial": spec["initial"]}
        formatter_key = spec.get("formatter")
        if formatter_key is not None:
            path_spec["textformat"] = FORMATTERS[formatter_key]
        paths[path] = path_spec
    return paths


def _is_unconfigured_host(host):
    return str(host).strip() in config.UNCONFIGURED_MODBUS_HOSTS


def main():
    handler = logging.StreamHandler()
    handler.addFilter(_RuntimeNoiseFilter())
    logging.basicConfig(
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=config.LOGGING,
        handlers=[handler],
        force=True,
    )
    logging.getLogger("pymodbus").setLevel(logging.WARNING)
    logging.getLogger("dbus").setLevel(logging.WARNING)

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    settings = HuaweiSUN2000Settings()
    logging.info(f"VRM pvinverter instance: {settings.get_vrm_instance()}")
    logging.info(
        f"Settings: ModbusHost '{settings.get('modbus_host')}', ModbusPort "
        f"'{settings.get('modbus_port')}', ModbusUnit '{settings.get('modbus_unit')}'"
    )
    logging.info(
        f"Settings: CustomName '{settings.get('custom_name')}', Position "
        f"'{settings.get('position')}', UpdateTimeMS "
        f"'{settings.get('update_time_ms')}', "
        f"PhaseTypeOverride '{settings.get('phase_type_override')}'"
    )
    logging.info(
        f"Settings: PowerCorrectionFactor "
        f"'{settings.get('power_correction_factor')}'"
    )

    while _is_unconfigured_host(settings.get("modbus_host")):
        # This catches the initial setting and allows the service
        # to be installed without configuring it first
        logging.warning(
            "Please configure the modbus host and other settings in the VenusOS GUI "
            f"(current setting: {settings.get('modbus_host')})"
        )
        # Running a mainloop means we'll be notified about config
        # changes and exit in that case
        # (which restarts the service)
        mainloop = GLib.MainLoop()
        mainloop.run()

    modbus = ModbusDataCollector2000Delux(
        host=settings.get("modbus_host"),
        port=settings.get("modbus_port"),
        modbus_unit=settings.get("modbus_unit"),
        power_correction_factor=settings.get("power_correction_factor"),
    )

    while True:
        staticdata = modbus.getStaticData(
            phase_type_override=settings.get("phase_type_override")
        )
        if staticdata is None:
            logging.error(
                "Didn't receive static data from modbus, error is above. Sleeping "
                "10 seconds before retrying."
            )
            # Again we sleep in the mainloop in order to pick up config changes
            mainloop = GLib.MainLoop()
            GLib.timeout_add(10000, exit_mainloop, mainloop)
            mainloop.run()
            continue
        break

    modbus.set_phase_type(staticdata.get("PhaseType"))

    try:
        logging.info("Starting up")

        dbuspath = _build_dbus_paths()

        DbusSun2000Service(
            servicename="com.victronenergy.pvinverter.sun2000",
            settings=settings,
            paths=dbuspath,
            productname=staticdata["Model"],
            model_id=staticdata["ModelID"],
            serialnumber=staticdata["SN"],
            partnumber=staticdata["PN"],
            firmware_version=staticdata["FirmwareVersion"],
            software_version=staticdata["SoftwareVersion"],
            hardware_version=staticdata["HardwareVersion"],
            phase_type=staticdata.get("PhaseType", "Unknown"),
            data_connector=modbus,
        )

        logging.info(
            "Connected to dbus, and switching over to GLib.MainLoop() "
            "(= event based)"
        )
        mainloop = GLib.MainLoop()
        oneshot_env = os.getenv("DBUS_HUAWEISUN2000_ONESHOT")
        if oneshot_env is not None:
            try:
                timeout_ms = max(int(oneshot_env), 100)
            except ValueError:
                timeout_ms = settings.get("update_time_ms") * 2

            def stop_loop():
                logging.info(
                    "Oneshot mode active, stopping main loop after %d ms",
                    timeout_ms,
                )
                mainloop.quit()
                return False

            GLib.timeout_add(timeout_ms, stop_loop)
        mainloop.run()
    except Exception as e:
        logging.critical("Error at %s", "main", exc_info=e)


if __name__ == "__main__":
    main()
