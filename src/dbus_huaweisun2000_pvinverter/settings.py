#!/usr/bin/env python3

import dbus
import logging
import os
import sys

sys.path.insert(
    1,
    os.path.join(
        os.path.dirname(__file__),
        "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python",
    ),
)

try:  # pragma: no cover - exercised only on target hardware
    from settingsdevice import SettingsDevice  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover - allows imports on dev systems

    class SettingsDevice:  # type: ignore
        def __init__(self, *args, supportedSettings=None, eventCallback=None, **kwargs):
            self._callback = eventCallback
            self._values = {
                key: setting[1] for key, setting in (supportedSettings or {}).items()
            }

            overrides = {
                "modbus_host": os.getenv("DBUS_HUAWEISUN2000_MODBUS_HOST"),
                "modbus_port": os.getenv("DBUS_HUAWEISUN2000_MODBUS_PORT"),
                "modbus_unit": os.getenv("DBUS_HUAWEISUN2000_MODBUS_UNIT"),
                "update_time_ms": os.getenv("DBUS_HUAWEISUN2000_UPDATE_TIME_MS"),
                "power_correction_factor": os.getenv(
                    "DBUS_HUAWEISUN2000_POWER_CORRECTION"
                ),
            }

            for key, value in overrides.items():
                if value is None:
                    continue
                if key in ("modbus_port", "modbus_unit", "update_time_ms"):
                    try:
                        self._values[key] = int(value)
                    except ValueError:
                        continue
                elif key == "power_correction_factor":
                    try:
                        self._values[key] = float(value)
                    except ValueError:
                        continue
                else:
                    self._values[key] = value

        def __getitem__(self, item):
            return self._values[item]

        def __setitem__(self, item, value):
            old_value = self._values.get(item)
            self._values[item] = value
            if self._callback is not None:
                self._callback(item, old_value, value)


class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)


class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)


class HuaweiSUN2000Settings(object):

    def __init__(self):
        # path, default value, min, max, logging silent or not
        supported_settings = {
            "modbus_host": [
                "/Settings/HuaweiSUN2000/ModbusHost",
                "192.168.5.186",
                "",
                "",
                0,
            ],
            "modbus_port": [
                "/Settings/HuaweiSUN2000/ModbusPort",
                502,
                1,
                65536,
                0,
            ],
            "modbus_unit": [
                "/Settings/HuaweiSUN2000/ModbusUnit",
                0,
                0,
                247,
                0,
            ],
            "custom_name": [
                "/Settings/HuaweiSUN2000/CustomName",
                "Huawei SUN2000",
                "",
                "",
                0,
            ],
            "position": [
                "/Settings/HuaweiSUN2000/Position",
                0,
                0,
                2,
                0,
            ],
            "update_time_ms": [
                "/Settings/HuaweiSUN2000/UpdateTimeMS",
                3000,
                1000,
                100000,
                0,
            ],
            "power_correction_factor": [
                "/Settings/HuaweiSUN2000/PowerCorrectionFactor",
                0.995,
                0.001,
                100.0,
                0,
            ],
            # "HuaweiSUN2000" is our unique id for the moment. This needs some more
            # thought if more than one inverter shall be supported.
            # Unfortunately we can't use the serial number, because we need the config
            # in order to get that one, so we have a catch-22.
            "vrm_instance": [
                "/Settings/Devices/HuaweiSUN2000/ClassAndVrmInstance",
                "pvinverter:1",
                "",
                "",
                0,
            ],
        }
        self.dbus_conn = self._dbusconnection()
        self.settings = SettingsDevice(
            bus=self.dbus_conn,
            supportedSettings=supported_settings,
            eventCallback=self._handle_changed_setting,
        )

    def _dbusconnection(self):
        return SessionBus() if "DBUS_SESSION_BUS_ADDRESS" in os.environ else SystemBus()

    def _handle_changed_setting(self, setting, oldvalue, newvalue):
        logging.info(
            f"setting changed, setting: {setting}, old: {oldvalue}, new: {newvalue}"
        )
        logging.info(
            "Exiting due to new setting. The service will get restarted and pick up "
            "the new setting."
        )
        # I consider this to be a bit of a hack, but it works for now. If there are
        # config changes, the service exits and gets restarted and thus picks up the
        # new settings values.
        sys.exit(0)

    def get(self, setting):
        return self.settings[setting]

    def set(self, setting, value):
        self.settings[setting] = value

    def get_vrm_instance(self):
        return int(self.settings["vrm_instance"].split(":")[1])
