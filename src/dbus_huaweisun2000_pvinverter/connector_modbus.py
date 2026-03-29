import logging
import time
from typing import Optional

from dbus.mainloop.glib import DBusGMainLoop

from . import config
from .metrics import DIRECT_REGISTER_METRICS
from .sun2000_modbus import datatypes
from .settings import HuaweiSUN2000Settings
from .sun2000_modbus import inverter
from .sun2000_modbus import registers

LOG = logging.getLogger(__name__)

PHASE_TYPE_SINGLE = "Single-phase"
PHASE_TYPE_THREE = "Three-phase"
PHASE_TYPE_UNKNOWN = "Unknown"

_SINGLE_PHASE_MODEL_MARKERS = ("-L1",)
_THREE_PHASE_MODEL_MARKERS = ("-M0", "-M1", "-M2", "-M3", "-M5", "-MB0", "-MAP0")


def _build_pv_string_specs():
    specs = []
    range_registers = {}
    for index in range(1, 25):
        voltage_register = getattr(
            registers.InverterEquipmentRegister, f"PV{index}Voltage"
        )
        current_register = getattr(
            registers.InverterEquipmentRegister, f"PV{index}Current"
        )
        voltage_key = f"_pv{index}_voltage"
        current_key = f"_pv{index}_current"
        range_registers[voltage_key] = voltage_register
        range_registers[current_key] = current_register
        specs.append((voltage_key, current_key, voltage_register, current_register))
    return tuple(specs), range_registers


_PV_STRING_SPECS, _PV_RANGE_REGISTERS = _build_pv_string_specs()
_MAIN_DATA_RANGE = {
    "start": 32064,
    "end": 32085,
    "registers": {
        "/Dc/Power": registers.InverterEquipmentRegister.InputPower,
        "/Ac/L1/Voltage": registers.InverterEquipmentRegister.PhaseAVoltage,
        "/Ac/L2/Voltage": registers.InverterEquipmentRegister.PhaseBVoltage,
        "/Ac/L3/Voltage": registers.InverterEquipmentRegister.PhaseCVoltage,
        "/Ac/L1/Current": registers.InverterEquipmentRegister.PhaseACurrent,
        "/Ac/L2/Current": registers.InverterEquipmentRegister.PhaseBCurrent,
        "/Ac/L3/Current": registers.InverterEquipmentRegister.PhaseCCurrent,
        "/Ac/Power": registers.InverterEquipmentRegister.ActivePower,
        "_power_factor": registers.InverterEquipmentRegister.PowerFactor,
        "_grid_frequency": registers.InverterEquipmentRegister.GridFrequency,
    },
}
_PV_INPUT_DATA_RANGE = {
    "start": 32016,
    "end": 32063,
    "optional_key": "_pv_inputs",
    "refresh_interval_s": config.PV_INPUT_REFRESH_INTERVAL_S,
    "registers": _PV_RANGE_REGISTERS,
}
_LIVE_COMBINED_DATA_RANGE = {
    "start": _PV_INPUT_DATA_RANGE["start"],
    "end": _MAIN_DATA_RANGE["end"],
}
_AUXILIARY_DATA_RANGES = (
    {
        "start": 30075,
        "end": 30076,
        "refresh_interval_s": 3600.0,
        "registers": {
            "/Ac/MaxPower": registers.InverterEquipmentRegister.MaximumActivePower,
        },
    },
    {
        "start": 32106,
        "end": 32107,
        "refresh_interval_s": 10.0,
        "registers": {
            "_energy_forward": (
                registers.InverterEquipmentRegister.AccumulatedEnergyYield
            ),
        },
    },
    {
        "start": 32114,
        "end": 32115,
        "refresh_interval_s": 10.0,
        "registers": {
            "_daily_energy_legacy": (
                registers.InverterEquipmentRegister.DailyEnergyYield
            ),
        },
    },
    {
        "start": 40562,
        "end": 40563,
        "refresh_interval_s": 10.0,
        "optional_key": "_daily_energy_realtime",
        "registers": {
            "_daily_energy_realtime": (
                registers.InverterEquipmentRegister.DailyEnergyYieldRealtime
            ),
        },
    },
)
_STATIC_DATA_SPECS = (
    {
        "name": "Model",
        "register": registers.InverterEquipmentRegister.Model,
        "default": "unknown",
        "formatted": True,
    },
    {
        "name": "SN",
        "register": registers.InverterEquipmentRegister.SN,
        "default": "unknown",
    },
    {
        "name": "PN",
        "register": registers.InverterEquipmentRegister.PN,
        "default": "unknown",
    },
    {
        "name": "ModelID",
        "register": registers.InverterEquipmentRegister.ModelID,
        "default": 0,
    },
    {
        "name": "FirmwareVersion",
        "register": registers.InverterEquipmentRegister.FirmwareVersion,
        "default": "unknown",
        "formatted": True,
    },
    {
        "name": "SoftwareVersion",
        "register": registers.InverterEquipmentRegister.SoftwareVersion,
        "default": "unknown",
    },
    {
        "name": "HardwareVersion",
        "register": registers.InverterEquipmentRegister.HardwareVersion,
        "default": "unknown",
    },
    {
        "name": "NumberOfPVStrings",
        "register": registers.InverterEquipmentRegister.NumberOfPVStrings,
        "default": 0,
    },
    {
        "name": "NumberOfMPPTrackers",
        "register": registers.InverterEquipmentRegister.NumberOfMPPTrackers,
        "default": 0,
    },
)


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
        if val is not None:
            LOG.warning("Modbus value is invalid: %s, using %s", val, default)
        return default


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        if val is not None:
            LOG.warning("Modbus value is invalid: %s, using %s", val, default)
        return default


def _clean_static_string(value, default):
    normalized = str(value or "").replace("\0", "").strip()
    return normalized or default


def _decode_range_register(payload, start_address, register):
    offset = (register.value.address - start_address) * 2
    length = register.value.quantity * 2
    raw_value = datatypes.decode(
        payload[offset : offset + length],
        register.value.data_type,
    )
    if register.value.gain is None:
        return raw_value
    return raw_value / register.value.gain


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
        time_fn=time.monotonic,
    ):
        self.invSun2000 = inverter_factory(
            host=host, port=port, modbus_unit=modbus_unit
        )
        self.power_correction_factor = power_correction_factor
        self._phase_divisor = 3  # default to three-phase; may be updated later
        self._phase_type: Optional[str] = None
        self._disabled_optional_keys = set()
        self._auxiliary_group_cache = {}
        self._auxiliary_group_updated_at = {}
        self._time_fn = time_fn

    def set_phase_type(self, phase_type: Optional[str]):
        """Adjust per-phase calculations based on inverter topology."""
        self._phase_type = phase_type
        normalized_phase_type = normalize_phase_type(phase_type)
        if normalized_phase_type == PHASE_TYPE_THREE:
            self._phase_divisor = 3
        else:
            self._phase_divisor = 1

    @staticmethod
    def _group_cache_key(group):
        return (group["start"], group["end"])

    def _read_range_group(self, group):
        optional_key = group.get("optional_key")
        cache_key = self._group_cache_key(group)
        cached_values = self._auxiliary_group_cache.get(cache_key)
        read_kwargs = self._build_group_read_kwargs(group, cached_values)

        if optional_key in self._disabled_optional_keys:
            return dict(cached_values or {})

        if self._can_reuse_cached_group(group, cached_values):
            return dict(cached_values)

        try:
            payload = self.invSun2000.read_range(
                group["start"],
                end_address=group["end"],
                **read_kwargs,
            )
        except inverter.UnsupportedRegisterError as err:
            if optional_key is not None:
                self._disable_optional_key(optional_key, group, err)
                return dict(cached_values or {})
            raise
        except Exception as err:
            LOG.debug(
                "Batch read %s-%s unavailable, falling back to single reads: %s",
                group["start"],
                group["end"],
                err,
            )
            if cached_values is not None:
                LOG.debug(
                    "Using cached values for range %s-%s after read failure",
                    group["start"],
                    group["end"],
                )
                return dict(cached_values)
            return {}

        values = self._decode_group_payload(
            group,
            payload,
            payload_start=group["start"],
        )
        self._cache_group_values(group, values)
        return values

    def _can_reuse_cached_group(self, group, cached_values):
        refresh_interval = group.get("refresh_interval_s")
        if refresh_interval is None or cached_values is None:
            return False

        updated_at = self._auxiliary_group_updated_at.get(self._group_cache_key(group))
        return (
            updated_at is not None and (self._time_fn() - updated_at) < refresh_interval
        )

    @staticmethod
    def _build_group_read_kwargs(group, cached_values):
        if group.get("refresh_interval_s") is not None and cached_values is not None:
            return {"retries": 1, "retry_delay": 0}
        return {}

    def _cache_group_values(self, group, values):
        if group.get("refresh_interval_s") is None or not values:
            return

        cache_key = self._group_cache_key(group)
        self._auxiliary_group_cache[cache_key] = dict(values)
        self._auxiliary_group_updated_at[cache_key] = self._time_fn()

    def _decode_group_payload(self, group, payload, *, payload_start):
        values = {}
        for key, register in group["registers"].items():
            try:
                values[key] = _decode_range_register(payload, payload_start, register)
            except Exception as err:
                LOG.warning(
                    "Could not decode %s from batch %s-%s: %s",
                    key,
                    group["start"],
                    group["end"],
                    err,
                )
        return values

    def _read_live_batch_values(self):
        pv_cached_values = self._auxiliary_group_cache.get(
            self._group_cache_key(_PV_INPUT_DATA_RANGE)
        )
        if _PV_INPUT_DATA_RANGE[
            "optional_key"
        ] not in self._disabled_optional_keys and not self._can_reuse_cached_group(
            _PV_INPUT_DATA_RANGE, pv_cached_values
        ):
            combined_kwargs = self._build_group_read_kwargs(
                _PV_INPUT_DATA_RANGE,
                pv_cached_values,
            )
            try:
                payload = self.invSun2000.read_range(
                    _LIVE_COMBINED_DATA_RANGE["start"],
                    end_address=_LIVE_COMBINED_DATA_RANGE["end"],
                    **combined_kwargs,
                )
            except Exception as err:
                LOG.debug(
                    "Combined live read %s-%s unavailable, "
                    "falling back to separate reads: %s",
                    _LIVE_COMBINED_DATA_RANGE["start"],
                    _LIVE_COMBINED_DATA_RANGE["end"],
                    err,
                )
            else:
                batch_values = self._decode_group_payload(
                    _MAIN_DATA_RANGE,
                    payload,
                    payload_start=_LIVE_COMBINED_DATA_RANGE["start"],
                )
                pv_values = self._decode_group_payload(
                    _PV_INPUT_DATA_RANGE,
                    payload,
                    payload_start=_LIVE_COMBINED_DATA_RANGE["start"],
                )
                self._cache_group_values(_PV_INPUT_DATA_RANGE, pv_values)
                batch_values.update(pv_values)
                return batch_values

        batch_values = self._read_range_group(_MAIN_DATA_RANGE)
        batch_values.update(self._read_range_group(_PV_INPUT_DATA_RANGE))
        return batch_values

    def _disable_optional_key(self, optional_key, group, err):
        if optional_key in self._disabled_optional_keys:
            return
        self._disabled_optional_keys.add(optional_key)
        LOG.info(
            "Disabling optional Modbus range %s-%s after hardware reject: %s",
            group["start"],
            group["end"],
            err,
        )

    def _read_register_value(self, key, register, batch_values):
        if key in batch_values:
            return batch_values[key]
        return self.invSun2000.read(register)

    def _read_daily_energy_wh(self, batch_values):
        last_error = None
        realtime_key = "_daily_energy_realtime"
        legacy_key = "_daily_energy_legacy"

        if realtime_key not in self._disabled_optional_keys:
            try:
                daily_yield_raw = self._read_register_value(
                    realtime_key,
                    registers.InverterEquipmentRegister.DailyEnergyYieldRealtime,
                    batch_values,
                )
                daily_yield_kwh = safe_float(daily_yield_raw, None)
                if daily_yield_kwh is not None:
                    return round(daily_yield_kwh * 1000.0, 1), None
            except inverter.UnsupportedRegisterError as err:
                self._disable_optional_key(
                    realtime_key,
                    _AUXILIARY_DATA_RANGES[-1],
                    err,
                )
                last_error = err
            except Exception as err:  # pragma: no cover - depends on hardware
                last_error = err

        try:
            daily_yield_raw = self._read_register_value(
                legacy_key,
                registers.InverterEquipmentRegister.DailyEnergyYield,
                batch_values,
            )
        except Exception as err:  # pragma: no cover - depends on hardware
            return None, err if last_error is None else last_error

        daily_yield_kwh = safe_float(daily_yield_raw, None)
        if daily_yield_kwh is None:
            return None, last_error
        return round(daily_yield_kwh * 1000.0, 1), last_error

    def _iter_pv_string_measurements(self, batch_values):
        if _PV_INPUT_DATA_RANGE["optional_key"] in self._disabled_optional_keys:
            return []

        measurements = []
        for (
            voltage_key,
            current_key,
            voltage_register,
            current_register,
        ) in _PV_STRING_SPECS:
            try:
                voltage = safe_float(
                    self._read_register_value(
                        voltage_key,
                        voltage_register,
                        batch_values,
                    ),
                    None,
                )
            except Exception:
                voltage = None

            try:
                current = safe_float(
                    self._read_register_value(
                        current_key,
                        current_register,
                        batch_values,
                    ),
                    None,
                )
            except Exception:
                current = None

            if voltage is None and current is None:
                continue
            measurements.append((voltage, current))

        return measurements

    def _derive_pv_metrics(self, data, batch_values):
        pv_voltage_sum = 0.0
        pv_current_sum = 0.0
        positive_voltages = []

        for voltage, current in self._iter_pv_string_measurements(batch_values):
            if voltage is not None and voltage > 0:
                positive_voltages.append(voltage)
            if (
                voltage is not None
                and voltage > 0
                and current is not None
                and current > 0
            ):
                pv_voltage_sum += voltage * current
                pv_current_sum += current

        pv_voltage = None
        if pv_current_sum > 0:
            pv_voltage = round(pv_voltage_sum / pv_current_sum, 1)
        elif positive_voltages:
            pv_voltage = round(sum(positive_voltages) / len(positive_voltages), 1)

        dc_power = safe_float(data.get("/Dc/Power"), None)
        if pv_voltage not in (None, 0):
            if dc_power is not None:
                pv_current = round(dc_power / pv_voltage, 1)
            elif pv_current_sum > 0:
                pv_current = round(pv_current_sum, 1)
            else:
                pv_current = None
        else:
            pv_current = None

        data["/Pv/V"] = pv_voltage
        data["/Pv/I"] = pv_current
        data["/Yield/Power"] = dc_power
        data["/Dc/0/Voltage"] = pv_voltage
        data["/Dc/0/Current"] = pv_current

    def _collect_batch_values(self):
        batch_values = self._read_live_batch_values()
        for group in _AUXILIARY_DATA_RANGES:
            batch_values.update(self._read_range_group(group))
        return batch_values

    def _populate_energy_metrics(self, data, batch_values):
        energy_forward_raw = self._read_register_value(
            "_energy_forward",
            registers.InverterEquipmentRegister.AccumulatedEnergyYield,
            batch_values,
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

        daily_yield_wh, last_error = self._read_daily_energy_wh(batch_values)

        if daily_yield_wh is None:
            if last_error is not None:
                LOG.warning("Could not read DailyEnergyYield: %s", last_error)
            data["/Ac/Energy/Today"] = None
            data["/Ac/L1/Energy/Today"] = None
            data["/Ac/L2/Energy/Today"] = None
            data["/Ac/L3/Energy/Today"] = None
            return

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

    def _populate_ac_summary_metrics(self, data, batch_values):
        data["/Ac/NumberOfPhases"] = self._phase_divisor

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
            self._read_register_value(
                "_grid_frequency",
                registers.InverterEquipmentRegister.GridFrequency,
                batch_values,
            ),
            None,
        )
        data["/Ac/L1/Frequency"] = freq
        data["/Ac/L2/Frequency"] = freq
        data["/Ac/L3/Frequency"] = freq

        cosphi = safe_float(
            self._read_register_value(
                "_power_factor",
                registers.InverterEquipmentRegister.PowerFactor,
                batch_values,
            )
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

    def getData(self):
        # The connect() method internally checks whether there's already a connection
        if not self.invSun2000.connect():
            LOG.error("Connection error Modbus TCP")
            return None

        data = {}
        batch_values = self._collect_batch_values()

        for path, spec in DIRECT_REGISTER_METRICS.items():
            raw = self._read_register_value(path, spec["register"], batch_values)
            data[path] = safe_float(raw, spec["initial"])

        # state1 is read but not used
        # state1 = self.invSun2000.read(registers.InverterEquipmentRegister.State1)
        # state1_int = safe_int(state1)
        # state1_string = ";".join(
        #     [val for key, val in state1Readable.items() if state1_int & key > 0]
        # )

        # data['/Ac/StatusCode'] = statuscode

        self._populate_energy_metrics(data, batch_values)
        self._populate_ac_summary_metrics(data, batch_values)
        self._derive_pv_metrics(data, batch_values)

        return data

    def getStaticData(self, phase_type_override=None):
        """
        Collects static information from the inverter using Modbus TCP.
        Returns a dictionary with keys such as SN, ModelID, Model, FirmwareVersion,
        SoftwareVersion, HardwareVersion, etc.
        If a value cannot be read, uses a typed default and logs a warning.
        """
        if not self.invSun2000.connect():
            LOG.error("Connection error Modbus TCP")
            return None

        data = {}

        def safe_read(register, name, default, formatted=False):
            try:
                value = (
                    self.invSun2000.read_formatted(register)
                    if formatted
                    else self.invSun2000.read(register)
                )
            except Exception as e:
                LOG.warning("Could not read %s: %s", name, e)
                return default

            if isinstance(default, str):
                return _clean_static_string(value, default)
            return value

        for spec in _STATIC_DATA_SPECS:
            data[spec["name"]] = safe_read(
                spec["register"],
                spec["name"],
                spec["default"],
                formatted=spec.get("formatted", False),
            )

        data["PhaseType"] = infer_phase_type(
            data["Model"], override=phase_type_override
        )

        LOG.info(
            "Static inverter info collected for model %s (SN %s, phase %s)",
            data["Model"],
            data["SN"],
            data["PhaseType"],
        )
        LOG.debug("Static inverter metadata: %s", data)
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
