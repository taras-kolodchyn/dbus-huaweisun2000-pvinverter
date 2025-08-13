# tests/test_formatters.py
# Self‑contained: provides minimal stubs and loads the target module by file path.

import sys
import pathlib
import importlib.util
import types

# ---- Stubs so the module imports without system deps (dbus/GLib/vedbus/etc) ----
# dbus + mainloop
_db = types.SimpleNamespace()
sys.modules["dbus"] = _db
_db.mainloop = types.SimpleNamespace()
sys.modules["dbus.mainloop"] = _db.mainloop
_db.mainloop.glib = types.SimpleNamespace(DBusGMainLoop=object)
sys.modules["dbus.mainloop.glib"] = _db.mainloop.glib

# GLib
_gi = types.SimpleNamespace(repository=types.SimpleNamespace())
sys.modules["gi"] = _gi
sys.modules["gi.repository"] = _gi.repository


class _GLib:
    @staticmethod
    def timeout_add(ms, func):
        return True


_gi.repository.GLib = _GLib
sys.modules["gi.repository.GLib"] = _GLib


# vedbus
class _FakeVeDbusService:
    def __init__(self, servicename, register=False):
        self.servicename = servicename
        self.registered = False
        self.paths = {}

    def add_path(
        self,
        path,
        initial=None,
        gettextcallback=None,
        writeable=False,
        onchangecallback=None,
    ):
        self.paths[path] = initial

    def register(self):
        self.registered = True

    def __enter__(self):
        return self.paths

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


vedbus = types.SimpleNamespace(VeDbusService=_FakeVeDbusService)
vedbus.__file__ = "vedbus.py"  # some code prints vedbus.__file__
sys.modules["vedbus"] = vedbus


# connector_modbus
class _FakeConnector:
    def __init__(self, *args, **kwargs):
        pass

    def getData(self):
        return {}


connector_modbus = types.SimpleNamespace(ModbusDataCollector2000Delux=_FakeConnector)
sys.modules["connector_modbus"] = connector_modbus


# settings
class _FakeSettings:
    def __init__(self, *args, **kwargs):
        pass

    def get_vrm_instance(self):
        return 123

    def get(self, key):
        return {
            "custom_name": "test_custom_name",
            "position": 1,
            "update_time_ms": 1000,
        }.get(key, None)


settings = types.SimpleNamespace(HuaweiSUN2000Settings=_FakeSettings)
sys.modules["settings"] = settings

# config
config = types.SimpleNamespace()
sys.modules["config"] = config
# -------------------------------------------------------------------------------

# Dynamically load the target module (filename has dashes, so we load by path)
MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "dbus-huaweisun2000-pvinverter.py"
)
spec = importlib.util.spec_from_file_location(
    "dbus_huaweisun2000_pvinverter", MODULE_PATH
)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

# ----------- Tests for pure formatting helpers (no D-Bus needed) ---------------


def test_format_kwh():
    assert m._format_kwh(None, 123.456) == "123.46 kWh"
    assert m._format_kwh(None, 0) == "0 kWh"
    assert m._format_kwh(None, None) is None


def test_format_a():
    assert m._format_a(None, 12.3456) == "12.3 A"
    assert m._format_a(None, 0) == "0 A"
    assert m._format_a(None, None) is None


def test_format_w():
    assert m._format_w(None, 1234.56) == "1234.6 W"
    assert m._format_w(None, 0) == "0 W"
    assert m._format_w(None, None) is None


def test_format_v():
    assert m._format_v(None, 230.123) == "230.1 V"
    assert m._format_v(None, 0) == "0 V"
    assert m._format_v(None, None) is None


def test_format_hz():
    assert m._format_hz(None, 50) == "50.0000Hz"
    assert m._format_hz(None, 50.123456) == "50.1235Hz"
    assert m._format_hz(None, None) is None


def test_format_n():
    assert m._format_n(None, 42) == "42"

    class Obj:
        def __str__(self):
            return "obj"

    assert m._format_n(None, Obj()) == "obj"
