from sun2000_modbus import inverter
from sun2000_modbus import registers
from dbus.mainloop.glib import DBusGMainLoop
from settings import HuaweiSUN2000Settings


def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        import logging

        logging.warning(f"Modbus value is invalid: '{val}', using {default}")
        return default


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        import logging

        logging.warning(f"Modbus value is invalid: '{val}', using {default}")
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
        host="192.168.5.186",
        port=502,
        modbus_unit=1,
        power_correction_factor=0.995,
    ):
        self.invSun2000 = inverter.Sun2000(
            host=host, port=port, modbus_unit=modbus_unit
        )
        self.power_correction_factor = power_correction_factor

    def getData(self):
        # The connect() method internally checks whether there's already a connection
        if not self.invSun2000.connect():
            print("Connection error Modbus TCP")
            return None

        data = {}

        dbuspath = {
            "/Ac/Power": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.ActivePower,
                "type": safe_float,
            },
            "/Ac/L1/Current": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.PhaseACurrent,
                "type": safe_float,
            },
            "/Ac/L1/Voltage": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.PhaseAVoltage,
                "type": safe_float,
            },
            "/Ac/L2/Current": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.PhaseBCurrent,
                "type": safe_float,
            },
            "/Ac/L2/Voltage": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.PhaseBVoltage,
                "type": safe_float,
            },
            "/Ac/L3/Current": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.PhaseCCurrent,
                "type": safe_float,
            },
            "/Ac/L3/Voltage": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.PhaseCVoltage,
                "type": safe_float,
            },
            "/Dc/Power": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.InputPower,
                "type": safe_float,
            },
            "/Ac/MaxPower": {
                "initial": 0,
                "sun2000": registers.InverterEquipmentRegister.MaximumActivePower,
                "type": safe_float,
            },
        }

        for k, v in dbuspath.items():
            s = v.get("sun2000")
            value_type = v.get("type", safe_float)
            raw = self.invSun2000.read(s)
            data[k] = value_type(raw, v.get("initial", 0))

        # state1 is read but not used
        # state1 = self.invSun2000.read(registers.InverterEquipmentRegister.State1)
        # state1_int = safe_int(state1)
        # state1_string = ";".join(
        #     [val for key, val in state1Readable.items() if state1_int & key > 0]
        # )

        # data['/Ac/StatusCode'] = statuscode

        energy_forward = self.invSun2000.read(
            registers.InverterEquipmentRegister.AccumulatedEnergyYield
        )
        data["/Ac/Energy/Forward"] = energy_forward
        # There is no Modbus register for the phases
        data["/Ac/L1/Energy/Forward"] = round(energy_forward / 3.0, 2)
        data["/Ac/L2/Energy/Forward"] = round(energy_forward / 3.0, 2)
        data["/Ac/L3/Energy/Forward"] = round(energy_forward / 3.0, 2)

        freq = self.invSun2000.read(registers.InverterEquipmentRegister.GridFrequency)
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

    def getStaticData(self):
        """
        Collects static information from the inverter using Modbus TCP.
        Returns a dictionary with keys such as SN, ModelID, Model, FirmwareVersion,
        SoftwareVersion, HardwareVersion, etc.
        If a value cannot be read, sets it to 'unknown' and logs a warning.
        """
        if not self.invSun2000.connect():
            print("Connection error Modbus TCP")
            return None

        import logging

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
                logging.warning(f"Could not read {name}: {e}")
                return "unknown"

        # Main fields
        data["Model"] = safe_read(
            registers.InverterEquipmentRegister.Model, "Model", formatted=True
        )
        model_str = data["Model"].upper()
        if "3" in model_str and "KTL" in model_str:
            data["PhaseType"] = "Three-phase"
        else:
            data["PhaseType"] = "Single-phase"

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
        logging.info("Static inverter info collected: " + str(data))
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
