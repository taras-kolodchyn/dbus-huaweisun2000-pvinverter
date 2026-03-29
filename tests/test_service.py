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
    DEFAULT_MODBUS_HOST="255.255.255.255",
    DEFAULT_MODBUS_PORT=502,
    DEFAULT_MODBUS_UNIT=0,
    DEFAULT_PHASE_TYPE_OVERRIDE="",
    DEFAULT_CUSTOM_NAME="Huawei SUN2000",
    DEFAULT_POSITION=0,
    DEFAULT_UPDATE_TIME_MS=1000,
    DEFAULT_POWER_CORRECTION_FACTOR=1.0,
    ADAPTIVE_POLLING_IDLE_POWER_THRESHOLD_W=50.0,
    ADAPTIVE_POLLING_IDLE_CONFIRM_CYCLES=3,
    ADAPTIVE_POLLING_IDLE_INTERVAL_MULTIPLIER=5,
    ADAPTIVE_POLLING_IDLE_MIN_UPDATE_TIME_MS=5000,
    ADAPTIVE_POLLING_IDLE_MAX_UPDATE_TIME_MS=10000,
    ADAPTIVE_POLLING_OFFLINE_MIN_UPDATE_TIME_MS=5000,
    ADAPTIVE_POLLING_OFFLINE_MAX_UPDATE_TIME_MS=30000,
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
sys.modules.pop("dbus", None)
sys.modules.pop("dbus.mainloop", None)
sys.modules.pop("dbus.mainloop.glib", None)
sys.modules.pop("gi", None)
sys.modules.pop("gi.repository", None)
sys.modules.pop("gi.repository.GLib", None)
sys.modules.pop("vedbus", None)
sys.modules.pop("dbus_huaweisun2000_pvinverter.connector_modbus", None)
sys.modules.pop("dbus_huaweisun2000_pvinverter.settings", None)
sys.modules.pop("dbus_huaweisun2000_pvinverter.config", None)

# ----------------------- Local fakes for runtime tests -------------------------


class FakeSettingsForService:
    def __init__(self):
        self.values = {
            "custom_name": "test_custom_name",
            "position": 1,
            "update_time_ms": 1000,
        }

    def get_vrm_instance(self):
        return 123

    def get(self, key):
        return self.values.get(key, None)

    def set(self, key, value):
        self.values[key] = value


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


class SequencedConnector:
    def __init__(self, samples):
        self.samples = list(samples)
        self.calls = 0

    def getData(self):
        index = min(self.calls, len(self.samples) - 1)
        self.calls += 1
        return dict(self.samples[index])


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


def build_service(
    timeout_impl=None,
    *,
    partnumber="X",
    hardware_version="0",
    model_id=0,
):
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
        partnumber=partnumber,
        hardware_version=hardware_version,
        model_id=model_id,
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
    assert p["/ProductId"] == 0
    assert p["/Position"] == 1
    assert p["/UpdateIndex"] == 0


def test_diagnostics_paths_exist_with_initial_defaults():
    svc, _ = build_service()
    p = svc._dbusservice.paths

    assert p["/Diagnostics/PollingMode"] == "active"
    assert p["/Diagnostics/SuccessCount"] == 0
    assert p["/Diagnostics/FailureCount"] == 0
    assert p["/Diagnostics/ConsecutiveFailures"] == 0
    assert p["/Diagnostics/LatencyAverage"] is None
    assert p["/Diagnostics/LastUpdateTimestamp"] is None


def test_product_id_uses_model_id_when_available():
    svc, _ = build_service(model_id=444.0)
    p = svc._dbusservice.paths

    assert p["/ProductId"] == 444
    assert p["/ModelID"] == 444.0


def test_hardware_version_falls_back_to_part_number_for_unknown_values():
    svc, _ = build_service(
        partnumber="01075485-002",
        hardware_version="unknown",
    )
    p = svc._dbusservice.paths

    assert p["/HardwareVersion"] == "01075485-002"


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


def test_update_success_populates_diagnostics():
    svc, _ = build_service()
    p = svc._dbusservice.paths

    assert svc._update() is False

    assert p["/Diagnostics/PollingMode"] == "active"
    assert p["/Diagnostics/SuccessCount"] == 1
    assert p["/Diagnostics/FailureCount"] == 0
    assert p["/Diagnostics/ConsecutiveFailures"] == 0
    assert isinstance(p["/Diagnostics/LatencyAverage"], (int, float))
    assert isinstance(p["/Diagnostics/LastUpdateTimestamp"], float)
    assert p["/Diagnostics/LatencyAverage"] == p["/Latency"]


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
    assert meta["/Position"]["writeable"] is True
    assert meta["/CustomName"]["writeable"] is True
    assert callable(meta["/Ac/Power"]["gettextcallback"])
    assert callable(meta["/Ac/Power"]["onchangecallback"])


def test_handlechangedvalue_accepts_changes():
    svc, _ = build_service()
    assert svc._handlechangedvalue("/any", 42) is True


def test_handlechangedvalue_updates_position_setting():
    svc, _ = build_service()

    assert svc._handlechangedvalue("/Position", 2) is True
    assert svc._settings.get("position") == 2


def test_handlechangedvalue_rejects_invalid_position():
    svc, _ = build_service()

    assert svc._handlechangedvalue("/Position", 99) is False
    assert svc._settings.get("position") == 1

    assert svc._handlechangedvalue("/Position", "bad") is False
    assert svc._settings.get("position") == 1


def test_handlechangedvalue_updates_custom_name_setting():
    svc, _ = build_service()

    assert svc._handlechangedvalue("/CustomName", "Huawei Field") is True
    assert svc._settings.get("custom_name") == "Huawei Field"


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
    assert svc._polling_mode == "offline"


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
    assert spy.calls[-1] == (5000, svc._update)
    assert svc._polling_mode == "offline"
    assert svc._update() is False
    assert spy.calls[-1] == (10000, svc._update)
    assert svc._polling_mode == "offline"


def test_update_failure_populates_diagnostics():
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

    p = svc._dbusservice.paths
    assert svc._update() is False

    assert p["/Diagnostics/PollingMode"] == "offline"
    assert p["/Diagnostics/SuccessCount"] == 0
    assert p["/Diagnostics/FailureCount"] == 1
    assert p["/Diagnostics/ConsecutiveFailures"] == 1
    assert p["/Diagnostics/LatencyAverage"] is None
    assert p["/Diagnostics/LastUpdateTimestamp"] is None


def test_update_success_recovers_from_offline_polling():
    class FlakyConnector:
        def __init__(self):
            self.calls = 0

        def getData(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("boom")
            return {"/Ac/Power": 200, "/Ac/Current": 1}

    settings = FakeSettingsForService()
    spy = SpyTimeout()
    svc = m.DbusSun2000Service(
        servicename="test.service",
        settings=settings,
        paths={
            "/Ac/Power": {"initial": 0, "textformat": m._format_w},
            "/Ac/Current": {"initial": 0, "textformat": m._format_a},
        },
        data_connector=FlakyConnector(),
        service_factory=FakeService,
        timeout_add=spy.add,
    )

    assert svc._update() is False
    assert svc._polling_mode == "offline"
    assert spy.calls[-1] == (5000, svc._update)

    assert svc._update() is False
    assert svc._polling_mode == "active"
    assert svc._failure_count == 0
    assert spy.calls[-1] == (1000, svc._update)


def test_update_diagnostics_tracks_rolling_latency_average():
    svc, _ = build_service()
    p = svc._dbusservice.paths

    svc._latency_samples.extend([100.0, 200.0, 300.0])
    svc._successful_update_count = 3
    svc._failed_update_count = 1
    svc._failure_count = 1
    svc._polling_mode = "offline"
    svc._last_update = 123.0

    svc._update_diagnostics(p)

    assert p["/Diagnostics/PollingMode"] == "offline"
    assert p["/Diagnostics/SuccessCount"] == 3
    assert p["/Diagnostics/FailureCount"] == 1
    assert p["/Diagnostics/ConsecutiveFailures"] == 1
    assert p["/Diagnostics/LatencyAverage"] == 200.0
    assert p["/Diagnostics/LastUpdateTimestamp"] == 123.0


def test_update_enters_idle_polling_after_consecutive_low_power_samples():
    settings = FakeSettingsForService()
    spy = SpyTimeout()
    connector = SequencedConnector(
        [
            {"/Ac/Power": 0, "/Ac/Current": 0, "/Dc/Power": 0, "/Yield/Power": 0},
            {"/Ac/Power": 0, "/Ac/Current": 0, "/Dc/Power": 0, "/Yield/Power": 0},
            {"/Ac/Power": 0, "/Ac/Current": 0, "/Dc/Power": 0, "/Yield/Power": 0},
        ]
    )
    svc = m.DbusSun2000Service(
        servicename="test.service",
        settings=settings,
        paths={
            "/Ac/Power": {"initial": 0, "textformat": m._format_w},
            "/Ac/Current": {"initial": 0, "textformat": m._format_a},
            "/Dc/Power": {"initial": 0, "textformat": m._format_w},
            "/Yield/Power": {"initial": 0, "textformat": m._format_w},
        },
        data_connector=connector,
        service_factory=FakeService,
        timeout_add=spy.add,
    )

    assert spy.calls == [(1000, svc._update)]
    assert svc._update() is False
    assert spy.calls[-1] == (1000, svc._update)
    assert svc._update() is False
    assert spy.calls[-1] == (1000, svc._update)
    assert svc._update() is False
    assert spy.calls[-1] == (5000, svc._update)
    assert svc._polling_mode == "idle"


def test_update_returns_to_active_polling_after_power_recovers():
    settings = FakeSettingsForService()
    spy = SpyTimeout()
    connector = SequencedConnector(
        [
            {"/Ac/Power": 0, "/Ac/Current": 0, "/Dc/Power": 0, "/Yield/Power": 0},
            {"/Ac/Power": 0, "/Ac/Current": 0, "/Dc/Power": 0, "/Yield/Power": 0},
            {"/Ac/Power": 0, "/Ac/Current": 0, "/Dc/Power": 0, "/Yield/Power": 0},
            {
                "/Ac/Power": 200,
                "/Ac/Current": 1,
                "/Dc/Power": 250,
                "/Yield/Power": 250,
            },
        ]
    )
    svc = m.DbusSun2000Service(
        servicename="test.service",
        settings=settings,
        paths={
            "/Ac/Power": {"initial": 0, "textformat": m._format_w},
            "/Ac/Current": {"initial": 0, "textformat": m._format_a},
            "/Dc/Power": {"initial": 0, "textformat": m._format_w},
            "/Yield/Power": {"initial": 0, "textformat": m._format_w},
        },
        data_connector=connector,
        service_factory=FakeService,
        timeout_add=spy.add,
    )

    svc._update()
    svc._update()
    svc._update()
    assert spy.calls[-1] == (5000, svc._update)
    assert svc._polling_mode == "idle"

    svc._update()
    assert spy.calls[-1] == (1000, svc._update)
    assert svc._polling_mode == "active"
    assert svc._idle_cycle_count == 0
