import pathlib
import sys
import types

import pytest


class _StubModbusTcpClient:
    def __init__(self, *args, **kwargs):
        pass


if "pymodbus" not in sys.modules:
    pymodbus = types.ModuleType("pymodbus")
    client_module = types.ModuleType("pymodbus.client")
    sync_module = types.ModuleType("pymodbus.client.sync")
    sync_module.ModbusTcpClient = _StubModbusTcpClient
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


SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import dbus_huaweisun2000_pvinverter.sun2000_modbus.inverter as inv  # noqa: E402
from dbus_huaweisun2000_pvinverter.sun2000_modbus import datatypes  # noqa: E402


class FakeModbusIOException(Exception):
    pass


class FakeConnectionException(FakeModbusIOException):
    pass


class Raised:
    def __init__(self, error):
        self.error = error


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def encode(self):
        return b"\x00" + self._payload


class FakeErrorResponse:
    def __init__(self, *, function_code=131, exception_code=2):
        self.function_code = function_code
        self.exception_code = exception_code

    def isError(self):
        return True

    def __str__(self):
        return (
            f"Exception Response({self.function_code}, 3, "
            f"exception={self.exception_code})"
        )


class FakeClient:
    def __init__(
        self,
        host,
        port,
        timeout,
        *,
        open_on_connect=True,
        open_sequence=None,
        read_results=None,
        close_error=None,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.open_on_connect = open_on_connect
        self.open_sequence = list(open_sequence or [])
        self.read_results = list(read_results or [])
        self.close_error = close_error
        self.connect_calls = 0
        self.close_calls = 0
        self.read_calls = []
        self._open = False

    def connect(self):
        self.connect_calls += 1
        if self.open_on_connect:
            self._open = True
        return self._open

    def close(self):
        self.close_calls += 1
        self._open = False
        if self.close_error is not None:
            raise self.close_error

    def is_socket_open(self):
        if self.open_sequence:
            self._open = self.open_sequence.pop(0)
        return self._open

    def read_holding_registers(self, address, quantity, unit):
        self.read_calls.append((address, quantity, unit))
        result = self.read_results.pop(0)
        if isinstance(result, Raised):
            raise result.error
        return result


def install_fake_client(monkeypatch, **client_kwargs):
    clients = []

    def factory(host, port, timeout):
        client = FakeClient(host, port, timeout, **client_kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(inv, "ModbusTcpClient", factory)
    monkeypatch.setattr(inv, "ModbusIOException", FakeModbusIOException)
    monkeypatch.setattr(inv, "ConnectionException", FakeConnectionException)
    return clients


def make_register(
    *,
    address=123,
    quantity=1,
    data_type=datatypes.DataType.UINT16_BE,
    gain=None,
    unit=None,
    mapping=None,
):
    return types.SimpleNamespace(
        value=types.SimpleNamespace(
            address=address,
            quantity=quantity,
            data_type=data_type,
            gain=gain,
            unit=unit,
            mapping=mapping,
        )
    )


def make_monotonic(values):
    iterator = iter(values)

    def _monotonic():
        return next(iterator)

    return _monotonic


def test_connect_waits_until_socket_opens(monkeypatch):
    clients = install_fake_client(
        monkeypatch,
        open_on_connect=False,
        open_sequence=[False, False, True],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    monkeypatch.setattr(inv.time, "monotonic", make_monotonic([0.0, 0.1]))

    inverter = inv.Sun2000("inverter.local", wait=1, timeout=1)

    assert inverter.connect() is True
    assert clients[0].connect_calls == 1


def test_connect_returns_false_when_socket_never_opens(monkeypatch):
    install_fake_client(
        monkeypatch,
        open_on_connect=False,
        open_sequence=[False, False, False],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    monkeypatch.setattr(inv.time, "monotonic", make_monotonic([0.0, 0.1, 0.3]))

    inverter = inv.Sun2000("inverter.local", wait=0.2, timeout=1)

    assert inverter.connect() is False


def test_read_raw_value_requires_open_connection(monkeypatch):
    install_fake_client(monkeypatch)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=0)

    with pytest.raises(ValueError, match="not connected"):
        inverter.read_raw_value(make_register())


def test_read_and_read_formatted_decode_gain_units_and_mapping(monkeypatch):
    payload = datatypes.encode(1234, datatypes.DataType.UINT16_BE)
    clients = install_fake_client(
        monkeypatch,
        read_results=[
            FakeResponse(payload),
            FakeResponse(payload),
            FakeResponse(payload),
            FakeResponse(datatypes.encode(7, datatypes.DataType.UINT16_BE)),
        ],
    )
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=0)
    clients[0]._open = True

    assert inverter.read(make_register(gain=10)) == 123.4
    assert inverter.read_formatted(make_register(gain=10, unit="W")) == "123.4 W"
    assert (
        inverter.read_formatted(make_register(mapping={1234: "grid-connected"}))
        == "grid-connected"
    )
    assert inverter.read_formatted(make_register(mapping={1: "standby"})) == "undefined"


def test_read_raw_value_retries_when_modbus_returns_exception_object(monkeypatch):
    clients = install_fake_client(
        monkeypatch,
        read_results=[
            FakeModbusIOException("unit did not respond"),
            FakeResponse(datatypes.encode(4660, datatypes.DataType.UINT16_BE)),
        ],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=0, retries=2)
    clients[0]._open = True

    value = inverter.read_raw_value(make_register(address=32080))

    assert value == 4660
    assert clients[0].close_calls == 1
    assert clients[0].connect_calls == 1
    assert clients[0].read_calls == [
        (32080, 1, inverter.modbus_unit),
        (32080, 1, inverter.modbus_unit),
    ]


def test_read_raw_value_raises_last_exception_after_retries(monkeypatch):
    clients = install_fake_client(
        monkeypatch,
        read_results=[
            FakeModbusIOException("timeout-1"),
            FakeModbusIOException("timeout-2"),
        ],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=0, retries=2)
    clients[0]._open = True

    with pytest.raises(FakeModbusIOException, match="timeout-2"):
        inverter.read_raw_value(make_register())


def test_read_raw_value_single_retry_override_skips_reconnect(monkeypatch):
    clients = install_fake_client(
        monkeypatch,
        read_results=[Raised(FakeConnectionException("link down"))],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=1, retries=3)
    clients[0]._open = True

    with pytest.raises(FakeConnectionException, match="link down"):
        inverter.read_raw_value(make_register(), retries=1, retry_delay=0)

    assert clients[0].close_calls == 0
    assert clients[0].connect_calls == 0
    assert clients[0].read_calls == [(123, 1, inverter.modbus_unit)]


def test_read_raw_value_fast_retry_skips_retry_and_post_connect_delay(monkeypatch):
    payload = datatypes.encode(42, datatypes.DataType.UINT16_BE)
    clients = install_fake_client(
        monkeypatch,
        read_results=[
            Raised(FakeConnectionException("Connection unexpectedly closed")),
            FakeResponse(payload),
        ],
    )
    sleep_calls = []
    monkeypatch.setattr(inv.time, "sleep", sleep_calls.append)
    inverter = inv.Sun2000("inverter.local", wait=2, retry_delay=1, retries=2)
    clients[0]._open = True

    value = inverter.read_raw_value(make_register(address=32080))

    assert value == 42
    assert sleep_calls == []
    assert clients[0].close_calls == 1
    assert clients[0].connect_calls == 1


def test_read_raw_value_generic_retry_keeps_backoff_and_post_connect_delay(monkeypatch):
    payload = datatypes.encode(42, datatypes.DataType.UINT16_BE)
    clients = install_fake_client(
        monkeypatch,
        read_results=[
            Raised(FakeConnectionException("timeout")),
            FakeResponse(payload),
        ],
    )
    sleep_calls = []
    monkeypatch.setattr(inv.time, "sleep", sleep_calls.append)
    inverter = inv.Sun2000("inverter.local", wait=2, retry_delay=1, retries=2)
    clients[0]._open = True

    value = inverter.read_raw_value(make_register(address=32080))

    assert value == 42
    assert sleep_calls == [1.0, 2.0]
    assert clients[0].close_calls == 1
    assert clients[0].connect_calls == 1


def test_read_raw_value_raises_unsupported_register_without_retry(monkeypatch):
    clients = install_fake_client(
        monkeypatch,
        read_results=[FakeErrorResponse(exception_code=2)],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=0, retries=3)
    clients[0]._open = True

    with pytest.raises(inv.UnsupportedRegisterError, match="123-123"):
        inverter.read_raw_value(make_register())

    assert clients[0].close_calls == 0
    assert clients[0].connect_calls == 0
    assert clients[0].read_calls == [(123, 1, inverter.modbus_unit)]


def test_read_range_validates_parameters(monkeypatch):
    install_fake_client(monkeypatch)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=0)

    with pytest.raises(ValueError, match="Either parameter quantity or end_address"):
        inverter.read_range(100)

    with pytest.raises(ValueError, match="Only one parameter quantity or end_address"):
        inverter.read_range(100, quantity=2, end_address=110)

    with pytest.raises(
        ValueError, match="end_address must be greater than start_address"
    ):
        inverter.read_range(100, end_address=100)

    with pytest.raises(ValueError, match="not connected"):
        inverter.read_range(100, quantity=2)


def test_read_range_retries_after_connection_exception(monkeypatch):
    payload = b"\x00\x01\x00\x02\x00\x03"
    clients = install_fake_client(
        monkeypatch,
        read_results=[
            Raised(FakeConnectionException("link down")),
            FakeResponse(payload),
        ],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=0, retries=2)
    clients[0]._open = True

    result = inverter.read_range(40000, end_address=40002)

    assert result == payload
    assert clients[0].close_calls == 1
    assert clients[0].connect_calls == 1
    assert clients[0].read_calls == [
        (40000, 3, inverter.modbus_unit),
        (40000, 3, inverter.modbus_unit),
    ]


def test_read_range_single_retry_override_skips_reconnect(monkeypatch):
    clients = install_fake_client(
        monkeypatch,
        read_results=[Raised(FakeConnectionException("link down"))],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=1, retries=3)
    clients[0]._open = True

    with pytest.raises(FakeConnectionException, match="link down"):
        inverter.read_range(40000, quantity=3, retries=1, retry_delay=0)

    assert clients[0].close_calls == 0
    assert clients[0].connect_calls == 0
    assert clients[0].read_calls == [(40000, 3, inverter.modbus_unit)]


def test_read_range_fast_retry_skips_retry_and_post_connect_delay(monkeypatch):
    payload = b"\x00\x01\x00\x02\x00\x03"
    clients = install_fake_client(
        monkeypatch,
        read_results=[
            Raised(
                FakeConnectionException("No Response received from the remote unit")
            ),
            FakeResponse(payload),
        ],
    )
    sleep_calls = []
    monkeypatch.setattr(inv.time, "sleep", sleep_calls.append)
    inverter = inv.Sun2000("inverter.local", wait=2, retry_delay=1, retries=2)
    clients[0]._open = True

    result = inverter.read_range(40000, end_address=40002)

    assert result == payload
    assert sleep_calls == []
    assert clients[0].close_calls == 1
    assert clients[0].connect_calls == 1


def test_read_range_generic_retry_keeps_backoff_and_post_connect_delay(monkeypatch):
    payload = b"\x00\x01\x00\x02\x00\x03"
    clients = install_fake_client(
        monkeypatch,
        read_results=[
            Raised(FakeConnectionException("timeout")),
            FakeResponse(payload),
        ],
    )
    sleep_calls = []
    monkeypatch.setattr(inv.time, "sleep", sleep_calls.append)
    inverter = inv.Sun2000("inverter.local", wait=2, retry_delay=1, retries=2)
    clients[0]._open = True

    result = inverter.read_range(40000, end_address=40002)

    assert result == payload
    assert sleep_calls == [1.0, 2.0]
    assert clients[0].close_calls == 1
    assert clients[0].connect_calls == 1


def test_read_range_raises_unsupported_register_without_retry(monkeypatch):
    clients = install_fake_client(
        monkeypatch,
        read_results=[FakeErrorResponse(exception_code=2)],
    )
    monkeypatch.setattr(inv.time, "sleep", lambda *_: None)
    inverter = inv.Sun2000("inverter.local", wait=0, retry_delay=0, retries=3)
    clients[0]._open = True

    with pytest.raises(inv.UnsupportedRegisterError, match="40562-40563"):
        inverter.read_range(40562, quantity=2)

    assert clients[0].close_calls == 0
    assert clients[0].connect_calls == 0
    assert clients[0].read_calls == [(40562, 2, inverter.modbus_unit)]
