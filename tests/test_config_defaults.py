import inspect
import logging
import pathlib
import sys
import types
import pytest


class _FakeModbusTcpClient:
    def __init__(self, *args, **kwargs):
        self._open = False

    def connect(self):
        self._open = True
        return True

    def close(self):
        self._open = False

    def is_socket_open(self):
        return self._open

    def read_holding_registers(self, *args, **kwargs):  # pragma: no cover - unused
        raise RuntimeError("Fake client should not be used in unit tests")


if "pymodbus" not in sys.modules:
    pymodbus = types.ModuleType("pymodbus")
    client_module = types.ModuleType("pymodbus.client")
    sync_module = types.ModuleType("pymodbus.client.sync")
    sync_module.ModbusTcpClient = _FakeModbusTcpClient
    exceptions_module = types.ModuleType("pymodbus.exceptions")
    exceptions_module.ModbusIOException = Exception
    exceptions_module.ConnectionException = Exception
    client_module.sync = sync_module
    pymodbus.client = client_module
    pymodbus.exceptions = exceptions_module
    sys.modules["pymodbus"] = pymodbus
    sys.modules["pymodbus.client"] = client_module
    sys.modules["pymodbus.client.sync"] = sync_module
    sys.modules["pymodbus.exceptions"] = exceptions_module


dbus_stub = types.SimpleNamespace()
sys.modules.setdefault("dbus", dbus_stub)


class _BusConnection(types.SimpleNamespace):
    TYPE_SYSTEM = "system"
    TYPE_SESSION = "session"

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)


dbus_stub.bus = types.SimpleNamespace(BusConnection=_BusConnection)
dbus_stub.mainloop = types.SimpleNamespace()
sys.modules.setdefault("dbus.mainloop", dbus_stub.mainloop)
dbus_stub.mainloop.glib = types.SimpleNamespace(DBusGMainLoop=object)
sys.modules.setdefault("dbus.mainloop.glib", dbus_stub.mainloop.glib)


SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from dbus_huaweisun2000_pvinverter import config  # noqa: E402
from dbus_huaweisun2000_pvinverter.connector_modbus import (  # noqa: E402
    ModbusDataCollector2000Delux,
)
from dbus_huaweisun2000_pvinverter.settings import HuaweiSUN2000Settings  # noqa: E402
from dbus_huaweisun2000_pvinverter import settings as settings_module  # noqa: E402
from dbus_huaweisun2000_pvinverter.sun2000_modbus.inverter import Sun2000  # noqa: E402


def test_runtime_modbus_defaults_are_shared():
    connector_params = inspect.signature(
        ModbusDataCollector2000Delux.__init__
    ).parameters
    inverter_params = inspect.signature(Sun2000.__init__).parameters
    settings = HuaweiSUN2000Settings()

    assert config.DEFAULT_MODBUS_HOST == "255.255.255.255"
    assert config.DEFAULT_MODBUS_PORT == 502
    assert config.DEFAULT_MODBUS_UNIT == 0
    assert config.DEFAULT_LOGLEVEL == "INFO"
    assert config.LOGGING == logging.INFO
    assert config.UNCONFIGURED_MODBUS_HOSTS == {"", "0.0.0.0", "255.255.255.255"}

    assert settings.get("modbus_host") == config.DEFAULT_MODBUS_HOST
    assert settings.get("modbus_port") == config.DEFAULT_MODBUS_PORT
    assert settings.get("modbus_unit") == config.DEFAULT_MODBUS_UNIT

    assert connector_params["host"].default == config.DEFAULT_MODBUS_HOST
    assert connector_params["port"].default == config.DEFAULT_MODBUS_PORT
    assert connector_params["modbus_unit"].default == config.DEFAULT_MODBUS_UNIT
    assert (
        connector_params["power_correction_factor"].default
        == config.DEFAULT_POWER_CORRECTION_FACTOR
    )

    assert inverter_params["port"].default == config.DEFAULT_MODBUS_PORT
    assert inverter_params["modbus_unit"].default == config.DEFAULT_MODBUS_UNIT


def test_docker_playground_documents_explicit_simulator_override():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    compose = (repo_root / "docker-compose.dev.yml").read_text()
    readme = (repo_root / "README.md").read_text()

    assert "MODBUS_SIM_PORT=15020" in compose
    assert "MODBUS_SIM_UNIT=1" in compose
    assert "DBUS_HUAWEISUN2000_MODBUS_PORT=15020" in compose
    assert "DBUS_HUAWEISUN2000_MODBUS_UNIT=1" in compose
    assert "defaults are host `255.255.255.255`, port `502`, and unit `0`." in readme
    assert "The playground pins the simulator to Modbus unit" in readme


def test_runtime_mutable_settings_do_not_request_restart(monkeypatch):
    settings = HuaweiSUN2000Settings()
    exit_calls = []

    monkeypatch.setattr(
        settings_module.sys, "exit", lambda code=0: exit_calls.append(code)
    )

    settings.set("position", 2)
    settings.set("custom_name", "Huawei Runtime")

    assert exit_calls == []


def test_connection_settings_still_request_restart(monkeypatch):
    settings = HuaweiSUN2000Settings()

    def _raise_exit(code=0):
        raise SystemExit(code)

    monkeypatch.setattr(settings_module.sys, "exit", _raise_exit)

    with pytest.raises(SystemExit):
        settings.set("modbus_host", "192.0.2.20")
