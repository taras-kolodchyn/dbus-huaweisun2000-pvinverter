import sys
import types
import pathlib
import logging


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

    def read_holding_registers(self, *args, **kwargs):  # pragma: no cover - not used
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


# Minimal dbus stub required by the connector module
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


# Ensure the src tree is importable
SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import dbus_huaweisun2000_pvinverter.connector_modbus as cm  # noqa: E402
from dbus_huaweisun2000_pvinverter.sun2000_modbus import datatypes  # noqa: E402
from dbus_huaweisun2000_pvinverter.sun2000_modbus import registers  # noqa: E402


class FakeSun2000:
    def __init__(self, *, values=None, **_):
        self.values = values or {}
        self._connected = False
        self.connect_calls = 0
        self.read_calls = []
        self.read_range_calls = []

    def connect(self):
        self.connect_calls += 1
        self._connected = True
        return True

    def read(self, register):
        self.read_calls.append(register)
        return self.values.get(register, 0)

    def read_formatted(self, register):
        return str(self.read(register))


def build_values():
    return {
        registers.InverterEquipmentRegister.ActivePower: 9000,
        registers.InverterEquipmentRegister.PhaseACurrent: 10,
        registers.InverterEquipmentRegister.PhaseAVoltage: 230,
        registers.InverterEquipmentRegister.PhaseBCurrent: 10,
        registers.InverterEquipmentRegister.PhaseBVoltage: 230,
        registers.InverterEquipmentRegister.PhaseCCurrent: 10,
        registers.InverterEquipmentRegister.PhaseCVoltage: 230,
        registers.InverterEquipmentRegister.InputPower: 9500,
        registers.InverterEquipmentRegister.MaximumActivePower: 10000,
        registers.InverterEquipmentRegister.AccumulatedEnergyYield: 123.45,
        registers.InverterEquipmentRegister.DailyEnergyYieldRealtime: 12.34,
        registers.InverterEquipmentRegister.DailyEnergyYield: 12.34,
        registers.InverterEquipmentRegister.GridFrequency: 50.0,
        registers.InverterEquipmentRegister.PowerFactor: 0.95,
    }


def _factory_with_values(values):
    def _factory(**_kwargs):
        return FakeSun2000(values=values)

    return _factory


def _encode_register_value(register, value):
    raw = (
        value
        if register.value.gain is None
        else int(round(value * register.value.gain))
    )
    return datatypes.encode(raw, register.value.data_type)


def _build_range_payload(start_address, end_address, values):
    payload = bytearray((end_address - start_address + 1) * 2)
    for register, value in values.items():
        encoded = _encode_register_value(register, value)
        offset = (register.value.address - start_address) * 2
        payload[offset : offset + len(encoded)] = encoded
    return bytes(payload)


def test_energy_distribution_updates_with_phase_type():
    values = build_values()
    factory = _factory_with_values(values)
    collector = cm.ModbusDataCollector2000Delux(
        host="1.2.3.4",
        inverter_factory=factory,
        power_correction_factor=1.0,
    )

    collector.set_phase_type("Three-phase")
    data_three = collector.getData()
    assert data_three["/Ac/Energy/Forward"] == 123.45
    assert data_three["/Ac/L1/Energy/Forward"] == round(123.45 / 3.0, 2)
    assert data_three["/Ac/L2/Energy/Forward"] == round(123.45 / 3.0, 2)
    assert data_three["/Ac/L3/Energy/Forward"] == round(123.45 / 3.0, 2)
    assert data_three["/Ac/Energy/Today"] == round(12.34 * 1000.0, 1)
    assert data_three["/Ac/L1/Energy/Today"] == round((12.34 * 1000.0) / 3.0, 1)
    assert data_three["/Ac/Voltage"] == 230.0
    assert data_three["/Ac/Current"] == round(10 + 10 + 10, 1)

    collector.set_phase_type("Single-phase")
    data_single = collector.getData()
    assert data_single["/Ac/L1/Energy/Forward"] == round(123.45, 2)
    assert data_single["/Ac/L2/Energy/Forward"] == 0.0
    assert data_single["/Ac/L3/Energy/Forward"] == 0.0
    assert data_single["/Ac/Energy/Today"] == round(12.34 * 1000.0, 1)
    assert data_single["/Ac/L1/Energy/Today"] == round(12.34 * 1000.0, 1)
    assert data_single["/Ac/Voltage"] == 230.0
    assert data_single["/Ac/Current"] == 30.0


def test_connector_handles_unexpected_register_missing():
    values = {
        registers.InverterEquipmentRegister.ActivePower: 100,
        registers.InverterEquipmentRegister.PhaseACurrent: 1,
        registers.InverterEquipmentRegister.PhaseAVoltage: 230,
        registers.InverterEquipmentRegister.InputPower: 110,
        registers.InverterEquipmentRegister.MaximumActivePower: 200,
        registers.InverterEquipmentRegister.AccumulatedEnergyYield: 9.0,
        registers.InverterEquipmentRegister.DailyEnergyYieldRealtime: 9.0,
        registers.InverterEquipmentRegister.GridFrequency: 50.0,
        registers.InverterEquipmentRegister.PowerFactor: 1.0,
    }
    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=_factory_with_values(values)
    )
    collector.set_phase_type(None)
    data = collector.getData()
    assert data["/Ac/Power"] == 100.0
    assert data["/Ac/L1/Energy/Forward"] == round(9.0, 2)
    assert data["/Ac/L2/Energy/Forward"] == 0.0
    assert data["/Ac/L3/Energy/Forward"] == 0.0
    assert data["/Ac/Energy/Today"] == round(9.0 * 1000.0, 1)
    assert data["/Ac/Voltage"] == 230.0
    assert data["/Ac/Current"] == 1.0


def test_daily_energy_falls_back_to_legacy_register():
    values = {
        registers.InverterEquipmentRegister.AccumulatedEnergyYield: 50.0,
        registers.InverterEquipmentRegister.DailyEnergyYield: 5.0,
        registers.InverterEquipmentRegister.GridFrequency: 50.0,
        registers.InverterEquipmentRegister.PhaseACurrent: 2.0,
        registers.InverterEquipmentRegister.PhaseAVoltage: 230,
        registers.InverterEquipmentRegister.PowerFactor: 1.0,
    }

    class LegacySun2000(FakeSun2000):
        def read(self, register):
            if register == registers.InverterEquipmentRegister.DailyEnergyYieldRealtime:
                raise RuntimeError("unsupported register")
            return super().read(register)

    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=lambda **_: LegacySun2000(values=values)
    )
    collector.set_phase_type("Single-phase")
    data = collector.getData()
    assert data["/Ac/Energy/Today"] == round(5.0 * 1000.0, 1)


def test_infer_phase_type_handles_common_huawei_suffixes():
    assert cm.infer_phase_type("SUN2000-3KTL-L1") == cm.PHASE_TYPE_SINGLE
    assert cm.infer_phase_type("SUN2000-6KTL-L1") == cm.PHASE_TYPE_SINGLE
    assert cm.infer_phase_type("SUN2000-8KTL-M1") == cm.PHASE_TYPE_THREE
    assert cm.infer_phase_type("SUN2000-30KTL-M3") == cm.PHASE_TYPE_THREE
    assert cm.infer_phase_type("SUN2000-17KTL-M5") == cm.PHASE_TYPE_THREE


def test_infer_phase_type_allows_manual_override():
    assert (
        cm.infer_phase_type("SUN2000-3KTL-L1", override="three-phase")
        == cm.PHASE_TYPE_THREE
    )
    assert (
        cm.infer_phase_type("SUN2000-30KTL-M3", override="single-phase")
        == cm.PHASE_TYPE_SINGLE
    )


def test_infer_phase_type_returns_unknown_for_unmapped_model():
    assert cm.infer_phase_type("SUN2000-FOO") == cm.PHASE_TYPE_UNKNOWN
    assert cm.infer_phase_type("") == cm.PHASE_TYPE_UNKNOWN


def test_get_static_data_uses_detected_phase_type_and_override():
    values = {
        registers.InverterEquipmentRegister.Model: "SUN2000-3KTL-L1",
        registers.InverterEquipmentRegister.ModelID: 101,
        registers.InverterEquipmentRegister.SN: "SN123",
        registers.InverterEquipmentRegister.PN: "PN123",
    }
    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=_factory_with_values(values)
    )

    staticdata = collector.getStaticData()
    assert staticdata["Model"] == "SUN2000-3KTL-L1"
    assert staticdata["PhaseType"] == cm.PHASE_TYPE_SINGLE

    override_staticdata = collector.getStaticData(phase_type_override="Three-phase")
    assert override_staticdata["PhaseType"] == cm.PHASE_TYPE_THREE


def test_get_static_data_uses_typed_fallbacks_for_missing_fields(caplog):
    class FailingStaticSun2000(FakeSun2000):
        def read(self, register):
            if register in {
                registers.InverterEquipmentRegister.SN,
                registers.InverterEquipmentRegister.PN,
                registers.InverterEquipmentRegister.ModelID,
                registers.InverterEquipmentRegister.SoftwareVersion,
                registers.InverterEquipmentRegister.HardwareVersion,
                registers.InverterEquipmentRegister.NumberOfPVStrings,
                registers.InverterEquipmentRegister.NumberOfMPPTrackers,
            }:
                raise RuntimeError(f"missing {register.name}")
            return super().read(register)

        def read_formatted(self, register):
            if register in {
                registers.InverterEquipmentRegister.Model,
                registers.InverterEquipmentRegister.FirmwareVersion,
            }:
                raise RuntimeError(f"missing {register.name}")
            return super().read_formatted(register)

    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=lambda **_: FailingStaticSun2000(values={})
    )

    with caplog.at_level(logging.WARNING, logger=cm.LOG.name):
        staticdata = collector.getStaticData()

    assert staticdata["Model"] == "unknown"
    assert staticdata["SN"] == "unknown"
    assert staticdata["PN"] == "unknown"
    assert staticdata["FirmwareVersion"] == "unknown"
    assert staticdata["SoftwareVersion"] == "unknown"
    assert staticdata["HardwareVersion"] == "unknown"
    assert staticdata["ModelID"] == 0
    assert staticdata["NumberOfPVStrings"] == 0
    assert staticdata["NumberOfMPPTrackers"] == 0
    assert staticdata["PhaseType"] == cm.PHASE_TYPE_UNKNOWN
    assert any("Could not read ModelID" in record.message for record in caplog.records)


def test_get_data_prefers_batch_reads_for_contiguous_registers():
    values = build_values()
    batch_payloads = {
        (32064, 32085): _build_range_payload(
            32064,
            32085,
            {
                registers.InverterEquipmentRegister.InputPower: values[
                    registers.InverterEquipmentRegister.InputPower
                ],
                registers.InverterEquipmentRegister.PhaseAVoltage: values[
                    registers.InverterEquipmentRegister.PhaseAVoltage
                ],
                registers.InverterEquipmentRegister.PhaseBVoltage: values[
                    registers.InverterEquipmentRegister.PhaseBVoltage
                ],
                registers.InverterEquipmentRegister.PhaseCVoltage: values[
                    registers.InverterEquipmentRegister.PhaseCVoltage
                ],
                registers.InverterEquipmentRegister.PhaseACurrent: values[
                    registers.InverterEquipmentRegister.PhaseACurrent
                ],
                registers.InverterEquipmentRegister.PhaseBCurrent: values[
                    registers.InverterEquipmentRegister.PhaseBCurrent
                ],
                registers.InverterEquipmentRegister.PhaseCCurrent: values[
                    registers.InverterEquipmentRegister.PhaseCCurrent
                ],
                registers.InverterEquipmentRegister.ActivePower: values[
                    registers.InverterEquipmentRegister.ActivePower
                ],
                registers.InverterEquipmentRegister.PowerFactor: values[
                    registers.InverterEquipmentRegister.PowerFactor
                ],
                registers.InverterEquipmentRegister.GridFrequency: values[
                    registers.InverterEquipmentRegister.GridFrequency
                ],
            },
        ),
        (30075, 30076): _build_range_payload(
            30075,
            30076,
            {
                registers.InverterEquipmentRegister.MaximumActivePower: values[
                    registers.InverterEquipmentRegister.MaximumActivePower
                ],
            },
        ),
        (32106, 32107): _build_range_payload(
            32106,
            32107,
            {
                registers.InverterEquipmentRegister.AccumulatedEnergyYield: values[
                    registers.InverterEquipmentRegister.AccumulatedEnergyYield
                ],
            },
        ),
        (32114, 32115): _build_range_payload(
            32114,
            32115,
            {
                registers.InverterEquipmentRegister.DailyEnergyYield: values[
                    registers.InverterEquipmentRegister.DailyEnergyYield
                ],
            },
        ),
        (40562, 40563): _build_range_payload(
            40562,
            40563,
            {
                registers.InverterEquipmentRegister.DailyEnergyYieldRealtime: values[
                    registers.InverterEquipmentRegister.DailyEnergyYieldRealtime
                ],
            },
        ),
    }

    class RangeSun2000(FakeSun2000):
        def read_range(self, start_address, quantity=0, end_address=0):
            end = end_address if end_address else start_address + quantity - 1
            self.read_range_calls.append((start_address, end))
            return batch_payloads[(start_address, end)]

    holder = {}

    def factory(**_kwargs):
        holder["instance"] = RangeSun2000(values=values)
        return holder["instance"]

    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=factory,
        power_correction_factor=1.0,
    )
    collector.set_phase_type("Three-phase")

    data = collector.getData()

    assert data["/Ac/Power"] == 9000.0
    assert data["/Dc/Power"] == 9500.0
    assert data["/Ac/MaxPower"] == 10000.0
    assert data["/Ac/Energy/Forward"] == 123.45
    assert data["/Ac/Energy/Today"] == 12340.0
    assert data["/Ac/L1/Frequency"] == 50.0
    assert holder["instance"].read_calls == []
    assert holder["instance"].read_range_calls == [
        (32064, 32085),
        (30075, 30076),
        (32106, 32107),
        (32114, 32115),
        (40562, 40563),
    ]


def test_get_data_falls_back_to_single_reads_when_batching_unavailable():
    values = build_values()

    class NoRangeSun2000(FakeSun2000):
        def read_range(self, start_address, quantity=0, end_address=0):
            raise RuntimeError("range reads unsupported")

    holder = {}

    def factory(**_kwargs):
        holder["instance"] = NoRangeSun2000(values=values)
        return holder["instance"]

    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=factory,
        power_correction_factor=1.0,
    )
    collector.set_phase_type("Single-phase")

    data = collector.getData()

    assert data["/Ac/Power"] == 9000.0
    assert data["/Ac/Energy/Today"] == 12340.0
    assert (
        registers.InverterEquipmentRegister.ActivePower in holder["instance"].read_calls
    )
    assert (
        registers.InverterEquipmentRegister.PowerFactor in holder["instance"].read_calls
    )


def test_get_data_disables_unsupported_optional_daily_realtime_range(caplog):
    values = build_values()
    batch_payloads = {
        (32064, 32085): _build_range_payload(
            32064,
            32085,
            {
                registers.InverterEquipmentRegister.InputPower: values[
                    registers.InverterEquipmentRegister.InputPower
                ],
                registers.InverterEquipmentRegister.PhaseAVoltage: values[
                    registers.InverterEquipmentRegister.PhaseAVoltage
                ],
                registers.InverterEquipmentRegister.PhaseBVoltage: values[
                    registers.InverterEquipmentRegister.PhaseBVoltage
                ],
                registers.InverterEquipmentRegister.PhaseCVoltage: values[
                    registers.InverterEquipmentRegister.PhaseCVoltage
                ],
                registers.InverterEquipmentRegister.PhaseACurrent: values[
                    registers.InverterEquipmentRegister.PhaseACurrent
                ],
                registers.InverterEquipmentRegister.PhaseBCurrent: values[
                    registers.InverterEquipmentRegister.PhaseBCurrent
                ],
                registers.InverterEquipmentRegister.PhaseCCurrent: values[
                    registers.InverterEquipmentRegister.PhaseCCurrent
                ],
                registers.InverterEquipmentRegister.ActivePower: values[
                    registers.InverterEquipmentRegister.ActivePower
                ],
                registers.InverterEquipmentRegister.PowerFactor: values[
                    registers.InverterEquipmentRegister.PowerFactor
                ],
                registers.InverterEquipmentRegister.GridFrequency: values[
                    registers.InverterEquipmentRegister.GridFrequency
                ],
            },
        ),
        (30075, 30076): _build_range_payload(
            30075,
            30076,
            {
                registers.InverterEquipmentRegister.MaximumActivePower: values[
                    registers.InverterEquipmentRegister.MaximumActivePower
                ],
            },
        ),
        (32106, 32107): _build_range_payload(
            32106,
            32107,
            {
                registers.InverterEquipmentRegister.AccumulatedEnergyYield: values[
                    registers.InverterEquipmentRegister.AccumulatedEnergyYield
                ],
            },
        ),
        (32114, 32115): _build_range_payload(
            32114,
            32115,
            {
                registers.InverterEquipmentRegister.DailyEnergyYield: values[
                    registers.InverterEquipmentRegister.DailyEnergyYield
                ],
            },
        ),
    }

    class OptionalRealtimeUnsupportedSun2000(FakeSun2000):
        def read_range(self, start_address, quantity=0, end_address=0):
            end = end_address if end_address else start_address + quantity - 1
            self.read_range_calls.append((start_address, end))
            if (start_address, end) == (40562, 40563):
                raise cm.inverter.UnsupportedRegisterError(
                    start_address,
                    end - start_address + 1,
                    "IllegalAddress",
                )
            return batch_payloads[(start_address, end)]

        def read(self, register):
            if register == registers.InverterEquipmentRegister.DailyEnergyYieldRealtime:
                raise AssertionError(
                    "Collector should stop probing the unsupported realtime register"
                )
            return super().read(register)

    holder = {}

    def factory(**_kwargs):
        holder["instance"] = OptionalRealtimeUnsupportedSun2000(values=values)
        return holder["instance"]

    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=factory,
        power_correction_factor=1.0,
    )
    collector.set_phase_type("Single-phase")

    with caplog.at_level(logging.INFO, logger=cm.LOG.name):
        first = collector.getData()
        second = collector.getData()

    assert first["/Ac/Energy/Today"] == 12340.0
    assert second["/Ac/Energy/Today"] == 12340.0
    assert holder["instance"].read_range_calls.count((40562, 40563)) == 1
    assert any(
        "Disabling optional Modbus range 40562-40563" in record.message
        for record in caplog.records
    )


def test_get_data_reuses_cached_auxiliary_ranges_between_refresh_windows():
    values = build_values()
    batch_payloads = {
        (32064, 32085): _build_range_payload(
            32064,
            32085,
            {
                registers.InverterEquipmentRegister.InputPower: values[
                    registers.InverterEquipmentRegister.InputPower
                ],
                registers.InverterEquipmentRegister.PhaseAVoltage: values[
                    registers.InverterEquipmentRegister.PhaseAVoltage
                ],
                registers.InverterEquipmentRegister.PhaseBVoltage: values[
                    registers.InverterEquipmentRegister.PhaseBVoltage
                ],
                registers.InverterEquipmentRegister.PhaseCVoltage: values[
                    registers.InverterEquipmentRegister.PhaseCVoltage
                ],
                registers.InverterEquipmentRegister.PhaseACurrent: values[
                    registers.InverterEquipmentRegister.PhaseACurrent
                ],
                registers.InverterEquipmentRegister.PhaseBCurrent: values[
                    registers.InverterEquipmentRegister.PhaseBCurrent
                ],
                registers.InverterEquipmentRegister.PhaseCCurrent: values[
                    registers.InverterEquipmentRegister.PhaseCCurrent
                ],
                registers.InverterEquipmentRegister.ActivePower: values[
                    registers.InverterEquipmentRegister.ActivePower
                ],
                registers.InverterEquipmentRegister.PowerFactor: values[
                    registers.InverterEquipmentRegister.PowerFactor
                ],
                registers.InverterEquipmentRegister.GridFrequency: values[
                    registers.InverterEquipmentRegister.GridFrequency
                ],
            },
        ),
        (30075, 30076): _build_range_payload(
            30075,
            30076,
            {
                registers.InverterEquipmentRegister.MaximumActivePower: values[
                    registers.InverterEquipmentRegister.MaximumActivePower
                ],
            },
        ),
        (32106, 32107): _build_range_payload(
            32106,
            32107,
            {
                registers.InverterEquipmentRegister.AccumulatedEnergyYield: values[
                    registers.InverterEquipmentRegister.AccumulatedEnergyYield
                ],
            },
        ),
        (32114, 32115): _build_range_payload(
            32114,
            32115,
            {
                registers.InverterEquipmentRegister.DailyEnergyYield: values[
                    registers.InverterEquipmentRegister.DailyEnergyYield
                ],
            },
        ),
        (40562, 40563): _build_range_payload(
            40562,
            40563,
            {
                registers.InverterEquipmentRegister.DailyEnergyYieldRealtime: values[
                    registers.InverterEquipmentRegister.DailyEnergyYieldRealtime
                ],
            },
        ),
    }

    class CachedRangeSun2000(FakeSun2000):
        def read_range(self, start_address, quantity=0, end_address=0):
            end = end_address if end_address else start_address + quantity - 1
            self.read_range_calls.append((start_address, end))
            return batch_payloads[(start_address, end)]

    holder = {}
    now = {"value": 0.0}

    def factory(**_kwargs):
        holder["instance"] = CachedRangeSun2000(values=values)
        return holder["instance"]

    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=factory,
        power_correction_factor=1.0,
        time_fn=lambda: now["value"],
    )
    collector.set_phase_type("Single-phase")

    first = collector.getData()
    now["value"] = 5.0
    second = collector.getData()

    assert first["/Ac/Energy/Today"] == 12340.0
    assert second["/Ac/Energy/Today"] == 12340.0
    assert holder["instance"].read_range_calls == [
        (32064, 32085),
        (30075, 30076),
        (32106, 32107),
        (32114, 32115),
        (40562, 40563),
        (32064, 32085),
    ]


def test_get_data_refreshes_cached_energy_ranges_after_interval():
    values = build_values()
    batch_payloads = {
        (32064, 32085): _build_range_payload(
            32064,
            32085,
            {
                registers.InverterEquipmentRegister.InputPower: values[
                    registers.InverterEquipmentRegister.InputPower
                ],
                registers.InverterEquipmentRegister.PhaseAVoltage: values[
                    registers.InverterEquipmentRegister.PhaseAVoltage
                ],
                registers.InverterEquipmentRegister.PhaseBVoltage: values[
                    registers.InverterEquipmentRegister.PhaseBVoltage
                ],
                registers.InverterEquipmentRegister.PhaseCVoltage: values[
                    registers.InverterEquipmentRegister.PhaseCVoltage
                ],
                registers.InverterEquipmentRegister.PhaseACurrent: values[
                    registers.InverterEquipmentRegister.PhaseACurrent
                ],
                registers.InverterEquipmentRegister.PhaseBCurrent: values[
                    registers.InverterEquipmentRegister.PhaseBCurrent
                ],
                registers.InverterEquipmentRegister.PhaseCCurrent: values[
                    registers.InverterEquipmentRegister.PhaseCCurrent
                ],
                registers.InverterEquipmentRegister.ActivePower: values[
                    registers.InverterEquipmentRegister.ActivePower
                ],
                registers.InverterEquipmentRegister.PowerFactor: values[
                    registers.InverterEquipmentRegister.PowerFactor
                ],
                registers.InverterEquipmentRegister.GridFrequency: values[
                    registers.InverterEquipmentRegister.GridFrequency
                ],
            },
        ),
        (30075, 30076): _build_range_payload(
            30075,
            30076,
            {
                registers.InverterEquipmentRegister.MaximumActivePower: values[
                    registers.InverterEquipmentRegister.MaximumActivePower
                ],
            },
        ),
        (32106, 32107): _build_range_payload(
            32106,
            32107,
            {
                registers.InverterEquipmentRegister.AccumulatedEnergyYield: values[
                    registers.InverterEquipmentRegister.AccumulatedEnergyYield
                ],
            },
        ),
        (32114, 32115): _build_range_payload(
            32114,
            32115,
            {
                registers.InverterEquipmentRegister.DailyEnergyYield: values[
                    registers.InverterEquipmentRegister.DailyEnergyYield
                ],
            },
        ),
        (40562, 40563): _build_range_payload(
            40562,
            40563,
            {
                registers.InverterEquipmentRegister.DailyEnergyYieldRealtime: values[
                    registers.InverterEquipmentRegister.DailyEnergyYieldRealtime
                ],
            },
        ),
    }

    class CachedRangeSun2000(FakeSun2000):
        def read_range(self, start_address, quantity=0, end_address=0):
            end = end_address if end_address else start_address + quantity - 1
            self.read_range_calls.append((start_address, end))
            return batch_payloads[(start_address, end)]

    holder = {}
    now = {"value": 0.0}

    def factory(**_kwargs):
        holder["instance"] = CachedRangeSun2000(values=values)
        return holder["instance"]

    collector = cm.ModbusDataCollector2000Delux(
        inverter_factory=factory,
        power_correction_factor=1.0,
        time_fn=lambda: now["value"],
    )
    collector.set_phase_type("Single-phase")

    collector.getData()
    now["value"] = 11.0
    collector.getData()

    assert holder["instance"].read_range_calls == [
        (32064, 32085),
        (30075, 30076),
        (32106, 32107),
        (32114, 32115),
        (40562, 40563),
        (32064, 32085),
        (32106, 32107),
        (32114, 32115),
        (40562, 40563),
    ]
