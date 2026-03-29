# tests/test_service.py
# Self‑contained: provides minimal stubs and loads the target module by file path.

import sys
import pathlib
import importlib.util
import types
import logging

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
sys.modules["dbus_huaweisun2000_pvinverter.connector_modbus"] = connector_modbus


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
sys.modules["dbus_huaweisun2000_pvinverter.settings"] = settings

# config
config = types.SimpleNamespace(
    LOGGING=10,
    UNCONFIGURED_MODBUS_HOSTS={"", "0.0.0.0", "255.255.255.255"},
)
sys.modules["dbus_huaweisun2000_pvinverter.config"] = config
# -------------------------------------------------------------------------------

# Dynamically load the target module from the src tree
SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

package_stub = types.ModuleType("dbus_huaweisun2000_pvinverter")
package_stub.__path__ = [str(SRC_DIR / "dbus_huaweisun2000_pvinverter")]
package_stub.__version__ = "0.0"
sys.modules.setdefault("dbus_huaweisun2000_pvinverter", package_stub)
MODULE_PATH = SRC_DIR / "dbus_huaweisun2000_pvinverter" / "main.py"
spec = importlib.util.spec_from_file_location(
    "dbus_huaweisun2000_pvinverter.main", MODULE_PATH
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


class FakeConnectorWithStatus:
    def __init__(self):
        self.calls = 0

    def getData(self):
        self.calls += 1
        return {
            "/Ac/Power": 42,
            "/Ac/Current": 2,
            "status_message": "All good",
        }


class SpyTimeout:
    def __init__(self):
        self.called = 0
        self.ms = None
        self.func = None
        self.calls = []

    def add(self, ms, func):
        self.called += 1
        self.ms = ms
        self.func = func
        self.calls.append((ms, func))
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


def test_build_dbus_paths_uses_shared_metric_schema():
    paths = m._build_dbus_paths()
    assert paths["/Ac/Power"]["initial"] == 0
    assert callable(paths["/Ac/Power"]["textformat"])
    assert paths["/Ac/MaxPower"]["initial"] == 20000
    assert paths["/Status"]["initial"] == ""
    assert "textformat" not in paths["/Status"]


def test_basic_required_paths_and_defaults():
    svc, _ = build_service()
    p = svc._dbusservice.paths
    assert p["/Role"] == "pvinverter"
    assert p["/StatusCode"] == 7
    assert p["/Connected"] == 1
    assert p["/Position"] == 1
    assert p["/UpdateIndex"] == 0


def test_runtime_noise_filter_drops_noisy_root_messages():
    filt = m._RuntimeNoiseFilter()
    dropped = logging.LogRecord(
        name="root",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="set /Ac/Power to 100",
        args=(),
        exc_info=None,
    )
    kept = logging.LogRecord(
        name="root",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Starting up",
        args=(),
        exc_info=None,
    )

    assert filt.filter(dropped) is False
    assert filt.filter(kept) is True


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
    assert svc._update() is False
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


def test_unconfigured_host_detection():
    assert m._is_unconfigured_host("255.255.255.255") is True
    assert m._is_unconfigured_host("0.0.0.0") is True
    assert m._is_unconfigured_host("") is True
    assert m._is_unconfigured_host("192.168.1.20") is False


def test_update_with_status_message_sets_status_and_latency():
    settings = FakeSettingsForService()
    svc = m.DbusSun2000Service(
        servicename="test.service",
        settings=settings,
        paths={
            "/Ac/Power": {"initial": 0, "textformat": m._format_w},
            "/Ac/Current": {"initial": 0, "textformat": m._format_a},
            "/Status": {"initial": ""},
        },
        data_connector=FakeConnectorWithStatus(),
        service_factory=FakeService,
        timeout_add=lambda ms, func: True,
    )

    p = svc._dbusservice.paths
    assert p["/Status"] == ""
    svc._update()
    assert p["/Status"] == "All good"
    assert p["/Connected"] == 1
    assert isinstance(p["/Latency"], (int, float))


def test_update_success_avoids_info_log_spam(caplog):
    svc, _ = build_service()

    with caplog.at_level(logging.INFO, logger=m.LOG.name):
        assert svc._update() is False

    assert not [record for record in caplog.records if record.levelno == logging.INFO]


def test_update_handles_none_data_and_disarms_connection():
    class NoneConnector:
        def getData(self):
            return None

    settings = FakeSettingsForService()
    svc = m.DbusSun2000Service(
        servicename="test.service",
        settings=settings,
        paths={
            "/Ac/Power": {"initial": 0, "textformat": m._format_w},
        },
        data_connector=NoneConnector(),
        service_factory=FakeService,
        timeout_add=lambda ms, func: True,
    )

    p = svc._dbusservice.paths
    before = p["/UpdateIndex"]
    assert svc._failure_count == 0
    assert svc._update() is False
    assert p["/UpdateIndex"] == before
    assert p["/Connected"] == 0
    assert p["/Status"].startswith("Update failed")
    assert svc._failure_count == 1


def test_update_failure_logs_warning_with_backoff(caplog):
    class RaisingConnector:
        def getData(self):
            raise RuntimeError("boom")

    settings = FakeSettingsForService()
    svc = m.DbusSun2000Service(
        servicename="test.service",
        settings=settings,
        paths={"/Ac/Power": {"initial": 0, "textformat": m._format_w}},
        data_connector=RaisingConnector(),
        service_factory=FakeService,
        timeout_add=lambda ms, func: True,
    )

    with caplog.at_level(logging.WARNING, logger=m.LOG.name):
        assert svc._update() is False

    warnings = [
        record.message for record in caplog.records if record.levelno == logging.WARNING
    ]
    assert any("Update failed for test.service" in message for message in warnings)
    assert any("retry in" in message for message in warnings)


def test_update_reschedules_after_completion():
    spy = SpyTimeout()
    svc, _ = build_service(timeout_impl=spy.add)

    assert spy.calls == [(1000, svc._update)]
    assert svc._update() is False
    assert spy.calls[-1] == (1000, svc._update)
    assert len(spy.calls) == 2


def test_update_failure_reschedules_with_exponential_backoff():
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

    assert spy.calls == [(1000, svc._update)]
    assert svc._update() is False
    assert spy.calls[-1] == (1000, svc._update)
    assert svc._update() is False
    assert spy.calls[-1] == (2000, svc._update)
