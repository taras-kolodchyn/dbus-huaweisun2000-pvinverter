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
from dbus_huaweisun2000_pvinverter.sun2000_modbus import registers  # noqa: E402


class FakeSun2000:
    def __init__(self, *, values=None, **_):
        self.values = values or {}
        self._connected = False
        self.connect_calls = 0

    def connect(self):
        self.connect_calls += 1
        self._connected = True
        return True

    def read(self, register):
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
        registers.InverterEquipmentRegister.AccumulatedEnergyYield: 123.0,
        registers.InverterEquipmentRegister.DailyEnergyYieldRealtime: 12.0,
        registers.InverterEquipmentRegister.DailyEnergyYield: 12.0,
        registers.InverterEquipmentRegister.GridFrequency: 50.0,
        registers.InverterEquipmentRegister.PowerFactor: 0.95,
    }


def _factory_with_values(values):
    def _factory(**_kwargs):
        return FakeSun2000(values=values)

    return _factory


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
    assert data_three["/Ac/Energy/Forward"] == 123.0
    assert data_three["/Ac/L1/Energy/Forward"] == round(123.0 / 3.0, 2)
    assert data_three["/Ac/L2/Energy/Forward"] == round(123.0 / 3.0, 2)
    assert data_three["/Ac/L3/Energy/Forward"] == round(123.0 / 3.0, 2)
    assert data_three["/Ac/Energy/Today"] == round(12.0 * 1000.0, 1)
    assert data_three["/Ac/L1/Energy/Today"] == round((12.0 * 1000.0) / 3.0, 1)
    assert data_three["/Ac/Voltage"] == 230.0
    assert data_three["/Ac/Current"] == round(10 + 10 + 10, 1)

    collector.set_phase_type("Single-phase")
    data_single = collector.getData()
    assert data_single["/Ac/L1/Energy/Forward"] == round(123.0, 2)
    assert data_single["/Ac/L2/Energy/Forward"] == 0.0
    assert data_single["/Ac/L3/Energy/Forward"] == 0.0
    assert data_single["/Ac/Energy/Today"] == round(12.0 * 1000.0, 1)
    assert data_single["/Ac/L1/Energy/Today"] == round(12.0 * 1000.0, 1)
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
