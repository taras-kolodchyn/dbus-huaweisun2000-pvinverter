# tests/test_service.py
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
class FakeService:
    def __init__(self, servicename, register=False):
        self.servicename = servicename
        self.registered = False
        self.paths = {}
        self.meta = {}

    def add_path(
        self,
        path,
        initial=None,
        gettextcallback=None,
        writeable=False,
        onchangecallback=None,
    ):
        self.paths[path] = initial
        self.meta[path] = {
            "writeable": writeable,
            "gettextcallback": gettextcallback,
            "onchangecallback": onchangecallback,
        }

    def register(self):
        self.registered = True

    def __enter__(self):
        return self.paths

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


vedbus = types.SimpleNamespace(VeDbusService=FakeService)
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


# settings for module import
class _FakeSettingsModule:
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


settings = types.SimpleNamespace(HuaweiSUN2000Settings=_FakeSettingsModule)
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

# ----------------------- Local fakes for runtime tests -------------------------


class FakeSettingsForService:
    def get_vrm_instance(self):
        return 123

    def get(self, key):
        return {
            "custom_name": "test_custom_name",
            "position": 1,
            "update_time_ms": 1000,
        }.get(key, None)


class FakeConnectorForService:
    def __init__(self):
        self.calls = 0

    def getData(self):
        self.calls += 1
        return {
            "/Ac/Power": 100,
            "/Ac/Current": 5,
        }


class SpyTimeout:
    def __init__(self):
        self.called = 0
        self.ms = None
        self.func = None

    def add(self, ms, func):
        self.called += 1
        self.ms = ms
        self.func = func
        return True


def build_service(timeout_impl=None):
    paths = {
        "/Ac/Power": {"initial": 0, "textformat": m._format_w},
        "/Ac/Current": {"initial": 0, "textformat": m._format_a},
    }
    settings = FakeSettingsForService()
    connector = FakeConnectorForService()
    if timeout_impl is None:

        def _noop(ms, func):
            return True

        timeout_impl = _noop
    svc = m.DbusSun2000Service(
        servicename="test.service",
        settings=settings,
        paths=paths,
        data_connector=connector,
        # new params are keyword-only in the class and safe to pass from tests
        service_factory=FakeService,
        timeout_add=timeout_impl,
    )
    return svc, connector


# ---------------------------------- Tests --------------------------------------


def test_register_called_and_timeout_scheduled():
    spy = SpyTimeout()
    svc, _ = build_service(timeout_impl=spy.add)
    assert isinstance(svc._dbusservice, FakeService)
    assert svc._dbusservice.registered is True
    assert spy.called == 1
    assert spy.ms == 1000
    assert callable(spy.func) and spy.func == svc._update


def test_mgmt_and_info_paths_exist():
    svc, _ = build_service()
    p = svc._dbusservice.paths
    assert "/Mgmt/ProcessName" in p
    assert "/Mgmt/ProcessVersion" in p
    assert "/Mgmt/Connection" in p
    assert "/DeviceInstance" in p
    assert "/ProductName" in p
    assert "/CustomName" in p
    assert "/FirmwareVersion" in p
    assert "/Info/SoftwareVersion" in p
    assert "/HardwareVersion" in p
    assert "/Info/PhaseType" in p


def test_basic_required_paths_and_defaults():
    svc, _ = build_service()
    p = svc._dbusservice.paths
    assert p["/Role"] == "pvinverter"
    assert p["/StatusCode"] == 7
    assert p["/Connected"] == 1
    assert p["/Position"] == 1
    assert p["/UpdateIndex"] == 0


def test_position_comes_from_settings():
    svc, _ = build_service()
    p = svc._dbusservice.paths
    assert p["/Position"] == 1  # from FakeSettingsForService


def test_update_writes_and_increments_index():
    svc, conn = build_service()
    p = svc._dbusservice.paths
    old = p["/UpdateIndex"]
    svc._update()
    assert p["/Ac/Power"] == 100
    assert p["/Ac/Current"] == 5
    assert p["/UpdateIndex"] == (old + 1) % 256
    assert conn.calls >= 1


def test_multiple_updates_wrap_beyond_255():
    svc, _ = build_service()
    p = svc._dbusservice.paths
    p["/UpdateIndex"] = 254
    svc._update()  # -> 255
    assert p["/UpdateIndex"] == 255
    svc._update()  # -> 0
    assert p["/UpdateIndex"] == 0
    svc._update()  # -> 1
    assert p["/UpdateIndex"] == 1


def test_update_does_not_increment_on_exception():
    class RaisingConnector:
        def getData(self):
            raise RuntimeError("boom")

    settings = FakeSettingsForService()
    spy = SpyTimeout()
    svc = m.DbusSun2000Service(
        servicename="test.service",
        settings=settings,
        paths={"/Ac/Power": {"initial": 0, "textformat": m._format_w}},
        data_connector=RaisingConnector(),
        service_factory=FakeService,
        timeout_add=spy.add,
    )
    p = svc._dbusservice.paths
    before = p["/UpdateIndex"]
    assert svc._update() is True  # method should be robust and return True
    assert p["/UpdateIndex"] == before


def test_writeable_flags_and_callbacks_present():
    svc, _ = build_service()
    meta = svc._dbusservice.meta
    assert meta["/Connected"]["writeable"] is True
    assert callable(meta["/Ac/Power"]["gettextcallback"])
    assert callable(meta["/Ac/Power"]["onchangecallback"])


def test_handlechangedvalue_accepts_changes():
    svc, _ = build_service()
    assert svc._handlechangedvalue("/any", 42) is True
