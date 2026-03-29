import logging
from typing import Optional

from dbus.mainloop.glib import DBusGMainLoop

from . import config
from .metrics import DIRECT_REGISTER_METRICS
from .settings import HuaweiSUN2000Settings
from .sun2000_modbus import inverter
from .sun2000_modbus import registers

LOG = logging.getLogger(__name__)

PHASE_TYPE_SINGLE = "Single-phase"
PHASE_TYPE_THREE = "Three-phase"
PHASE_TYPE_UNKNOWN = "Unknown"

_SINGLE_PHASE_MODEL_MARKERS = ("-L1",)
_THREE_PHASE_MODEL_MARKERS = ("-M0", "-M1", "-M2", "-M3", "-M5", "-MB0", "-MAP0")


def normalize_phase_type(value) -> Optional[str]:
    if value is None:
        return None

    normalized = str(value).strip().lower()
    if normalized in ("", "auto", "unknown"):
        return None
    if normalized in ("single", "single-phase", "1", "1-phase"):
        return PHASE_TYPE_SINGLE
    if normalized in ("three", "three-phase", "3", "3-phase"):
        return PHASE_TYPE_THREE
    return None


def infer_phase_type(model, override=None) -> str:
    normalized_override = normalize_phase_type(override)
    if normalized_override is not None:
        return normalized_override

    if override not in (None, "", "Auto", "auto", "Unknown", "unknown"):
        LOG.warning(
            "Unsupported phase type override %r, falling back to auto", override
        )

    model_str = str(model or "").replace("\0", "").upper().strip()
    if not model_str:
        return PHASE_TYPE_UNKNOWN

    if any(marker in model_str for marker in _SINGLE_PHASE_MODEL_MARKERS):
        return PHASE_TYPE_SINGLE

    if any(marker in model_str for marker in _THREE_PHASE_MODEL_MARKERS):
        return PHASE_TYPE_THREE

    if "KTL" in model_str:
        return PHASE_TYPE_THREE

    return PHASE_TYPE_UNKNOWN


def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        LOG.warning("Modbus value is invalid: %s, using %s", val, default)
        return default


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        LOG.warning("Modbus value is invalid: %s, using %s", val, default)
        return default


state1Readable = {
    1: "standby",
    2: "grid connected",
    4: "grid connected normaly",
    8: "grid connection with derating due to power rationing",
    16: (
        "grid connection with derating due to internal causes of the solar " "inverter"
    ),
    32: "normal stop",
    64: "stop due to faults",
    128: "stop due to power",
    256: "shutdown",
    512: "spot check",
}
state2Readable = {
    1: "locking status (0:locked;1:unlocked)",
    2: "pv connection stauts (0:disconnected;1:conncted)",
    4: "grid connected normaly",
    8: "grid connection with derating due to power rationing",
    16: (
        "grid connection with derating due to internal causes of the solar " "inverter"
    ),
    32: "normal stop",
    64: "stop due to faults",
    128: "stop due to power",
    256: "shutdown",
    512: "spot check",
}
state3Readable = {
    1: "off-grid(0:on-grid;1:off-grid",
    2: "off-grid-switch(0:disable;1:enable)",
}
alert1Readable = {1: "", 2: ""}


class ModbusDataCollector2000Delux:
    def __init__(
        self,
        host=config.DEFAULT_MODBUS_HOST,
        port=config.DEFAULT_MODBUS_PORT,
        modbus_unit=config.DEFAULT_MODBUS_UNIT,
        power_correction_factor=config.DEFAULT_POWER_CORRECTION_FACTOR,
        inverter_factory=inverter.Sun2000,
    ):
        self.invSun2000 = inverter_factory(
            host=host, port=port, modbus_unit=modbus_unit
        )
        self.power_correction_factor = power_correction_factor
        self._phase_divisor = 3  # default to three-phase; may be updated later
        self._phase_type: Optional[str] = None

    def set_phase_type(self, phase_type: Optional[str]):
        """Adjust per-phase calculations based on inverter topology."""
        self._phase_type = phase_type
        normalized_phase_type = normalize_phase_type(phase_type)
        if normalized_phase_type == PHASE_TYPE_THREE:
            self._phase_divisor = 3
        else:
            self._phase_divisor = 1

    def getData(self):
        # The connect() method internally checks whether there's already a connection
        if not self.invSun2000.connect():
            LOG.error("Connection error Modbus TCP")
            return None

        data = {}

        for path, spec in DIRECT_REGISTER_METRICS.items():
            raw = self.invSun2000.read(spec["register"])
            data[path] = safe_float(raw, spec["initial"])

        # state1 is read but not used
        # state1 = self.invSun2000.read(registers.InverterEquipmentRegister.State1)
        # state1_int = safe_int(state1)
        # state1_string = ";".join(
        #     [val for key, val in state1Readable.items() if state1_int & key > 0]
        # )

        # data['/Ac/StatusCode'] = statuscode

        energy_forward_raw = self.invSun2000.read(
            registers.InverterEquipmentRegister.AccumulatedEnergyYield
        )
        energy_forward = safe_float(energy_forward_raw, 0.0)
        data["/Ac/Energy/Forward"] = energy_forward
        if self._phase_divisor == 3:
            per_phase_energy = round(energy_forward / 3.0, 2)
            data["/Ac/L1/Energy/Forward"] = per_phase_energy
            data["/Ac/L2/Energy/Forward"] = per_phase_energy
            data["/Ac/L3/Energy/Forward"] = per_phase_energy
        else:
            per_phase_energy = round(energy_forward, 2)
            data["/Ac/L1/Energy/Forward"] = per_phase_energy
            data["/Ac/L2/Energy/Forward"] = 0.0
            data["/Ac/L3/Energy/Forward"] = 0.0

        daily_registers = (
            registers.InverterEquipmentRegister.DailyEnergyYieldRealtime,
            registers.InverterEquipmentRegister.DailyEnergyYield,
        )

        daily_yield_wh = None
        last_error = None
        for candidate in daily_registers:
            try:
                daily_yield_raw = self.invSun2000.read(candidate)
            except Exception as err:  # pragma: no cover - depends on hardware
                last_error = err
                continue
            daily_yield_kwh = safe_float(daily_yield_raw, None)
            if daily_yield_kwh is None:
                continue
            daily_yield_wh = round(daily_yield_kwh * 1000.0, 1)
            break

        if daily_yield_wh is None:
            if last_error is not None:
                LOG.warning("Could not read DailyEnergyYield: %s", last_error)
            data["/Ac/Energy/Today"] = None
            data["/Ac/L1/Energy/Today"] = None
            data["/Ac/L2/Energy/Today"] = None
            data["/Ac/L3/Energy/Today"] = None
        else:
            data["/Ac/Energy/Today"] = daily_yield_wh
            if self._phase_divisor == 3:
                per_phase_today = round(daily_yield_wh / 3.0, 1)
                data["/Ac/L1/Energy/Today"] = per_phase_today
                data["/Ac/L2/Energy/Today"] = per_phase_today
                data["/Ac/L3/Energy/Today"] = per_phase_today
            else:
                data["/Ac/L1/Energy/Today"] = daily_yield_wh
                data["/Ac/L2/Energy/Today"] = 0.0
                data["/Ac/L3/Energy/Today"] = 0.0

        if self._phase_divisor == 1:
            data["/Ac/Voltage"] = safe_float(data.get("/Ac/L1/Voltage"), None)
        else:
            voltages = [
                safe_float(data.get("/Ac/L1/Voltage"), None),
                safe_float(data.get("/Ac/L2/Voltage"), None),
                safe_float(data.get("/Ac/L3/Voltage"), None),
            ]
            valid_voltages = [v for v in voltages if v not in (None, 0.0)]
            data["/Ac/Voltage"] = (
                round(sum(valid_voltages) / len(valid_voltages), 1)
                if valid_voltages
                else None
            )

        currents = [
            safe_float(data.get("/Ac/L1/Current"), None),
            safe_float(data.get("/Ac/L2/Current"), None),
            safe_float(data.get("/Ac/L3/Current"), None),
        ]
        if any(c is not None for c in currents):
            data["/Ac/Current"] = round(sum(c or 0.0 for c in currents), 1)
        else:
            data["/Ac/Current"] = None

        freq = safe_float(
            self.invSun2000.read(registers.InverterEquipmentRegister.GridFrequency),
            None,
        )
        data["/Ac/L1/Frequency"] = freq
        data["/Ac/L2/Frequency"] = freq
        data["/Ac/L3/Frequency"] = freq

        cosphi = safe_float(
            self.invSun2000.read(registers.InverterEquipmentRegister.PowerFactor)
        )
        data["/Ac/L1/Power"] = (
            cosphi
            * float(data["/Ac/L1/Voltage"])
            * float(data["/Ac/L1/Current"])
            * self.power_correction_factor
        )
        data["/Ac/L2/Power"] = (
            cosphi
            * float(data["/Ac/L2/Voltage"])
            * float(data["/Ac/L2/Current"])
            * self.power_correction_factor
        )
        data["/Ac/L3/Power"] = (
            cosphi
            * float(data["/Ac/L3/Voltage"])
            * float(data["/Ac/L3/Current"])
            * self.power_correction_factor
        )

        return data

    def getStaticData(self, phase_type_override=None):
        """
        Collects static information from the inverter using Modbus TCP.
        Returns a dictionary with keys such as SN, ModelID, Model, FirmwareVersion,
        SoftwareVersion, HardwareVersion, etc.
        If a value cannot be read, sets it to 'unknown' and logs a warning.
        """
        if not self.invSun2000.connect():
            LOG.error("Connection error Modbus TCP")
            return None

        data = {}

        def safe_read(register, name, formatted=False):
            try:
                if formatted:
                    return str(self.invSun2000.read_formatted(register)).replace(
                        "\0", ""
                    )
                else:
                    return self.invSun2000.read(register)
            except Exception as e:
                LOG.warning("Could not read %s: %s", name, e)
                return "unknown"

        # Main fields
        data["Model"] = safe_read(
            registers.InverterEquipmentRegister.Model, "Model", formatted=True
        )
        data["PhaseType"] = infer_phase_type(
            data["Model"], override=phase_type_override
        )

        data["SN"] = safe_read(registers.InverterEquipmentRegister.SN, "SN")
        data["PN"] = safe_read(registers.InverterEquipmentRegister.PN, "PN")
        data["ModelID"] = safe_read(
            registers.InverterEquipmentRegister.ModelID, "ModelID"
        )
        data["FirmwareVersion"] = safe_read(
            registers.InverterEquipmentRegister.FirmwareVersion,
            "FirmwareVersion",
            formatted=True,
        )
        data["SoftwareVersion"] = safe_read(
            registers.InverterEquipmentRegister.SoftwareVersion, "SoftwareVersion"
        )
        data["HardwareVersion"] = safe_read(
            registers.InverterEquipmentRegister.HardwareVersion, "HardwareVersion"
        )
        data["NumberOfPVStrings"] = safe_read(
            registers.InverterEquipmentRegister.NumberOfPVStrings, "NumberOfPVStrings"
        )
        data["NumberOfMPPTrackers"] = safe_read(
            registers.InverterEquipmentRegister.NumberOfMPPTrackers,
            "NumberOfMPPTrackers",
        )

        # Log all static data for debugging purposes
        LOG.info("Static inverter info collected: %s", data)
        return data


# Just for testing
if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    settings = HuaweiSUN2000Settings()
    inverter = inverter.Sun2000(
        host=settings.get("modbus_host"),
        port=settings.get("modbus_port"),
        modbus_unit=settings.get("modbus_unit"),
    )
    inverter.connect()
    if inverter.isConnected():

        attrs = (
            getattr(registers.InverterEquipmentRegister, name)
            for name in dir(registers.InverterEquipmentRegister)
        )
        datata = dict()
        for f in attrs:
            if isinstance(f, registers.InverterEquipmentRegister):
                datata[f.name] = inverter.read_formatted(f)

        for k, v in datata.items():
            print(f"{k}: {v}")
