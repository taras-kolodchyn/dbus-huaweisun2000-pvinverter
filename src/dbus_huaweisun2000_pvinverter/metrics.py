from .sun2000_modbus import registers


def _metric(initial, formatter=None, register=None):
    spec = {"initial": initial}
    if formatter is not None:
        spec["formatter"] = formatter
    if register is not None:
        spec["register"] = register
    return spec


DIRECT_REGISTER_METRICS = {
    "/Ac/Power": _metric(
        0, formatter="w", register=registers.InverterEquipmentRegister.ActivePower
    ),
    "/Ac/L1/Current": _metric(
        0, formatter="a", register=registers.InverterEquipmentRegister.PhaseACurrent
    ),
    "/Ac/L1/Voltage": _metric(
        0, formatter="v", register=registers.InverterEquipmentRegister.PhaseAVoltage
    ),
    "/Ac/L2/Current": _metric(
        0, formatter="a", register=registers.InverterEquipmentRegister.PhaseBCurrent
    ),
    "/Ac/L2/Voltage": _metric(
        0, formatter="v", register=registers.InverterEquipmentRegister.PhaseBVoltage
    ),
    "/Ac/L3/Current": _metric(
        0, formatter="a", register=registers.InverterEquipmentRegister.PhaseCCurrent
    ),
    "/Ac/L3/Voltage": _metric(
        0, formatter="v", register=registers.InverterEquipmentRegister.PhaseCVoltage
    ),
    "/Dc/Power": _metric(
        0, formatter="w", register=registers.InverterEquipmentRegister.InputPower
    ),
    "/Ac/MaxPower": _metric(
        20000,
        formatter="w",
        register=registers.InverterEquipmentRegister.MaximumActivePower,
    ),
}

DERIVED_SERVICE_METRICS = {
    "/Ac/Current": _metric(0, formatter="a"),
    "/Ac/Voltage": _metric(0, formatter="v"),
    "/Ac/Energy/Forward": _metric(None, formatter="kwh"),
    "/Ac/Energy/Today": _metric(None, formatter="wh"),
    "/Ac/L1/Power": _metric(0, formatter="w"),
    "/Ac/L1/Frequency": _metric(None, formatter="hz"),
    "/Ac/L1/Energy/Forward": _metric(None, formatter="kwh"),
    "/Ac/L1/Energy/Today": _metric(None, formatter="wh"),
    "/Ac/StatusCode": _metric(0, formatter="n"),
    "/Ac/L2/Power": _metric(0, formatter="w"),
    "/Ac/L2/Frequency": _metric(None, formatter="hz"),
    "/Ac/L2/Energy/Forward": _metric(None, formatter="kwh"),
    "/Ac/L2/Energy/Today": _metric(None, formatter="wh"),
    "/Ac/L3/Power": _metric(0, formatter="w"),
    "/Ac/L3/Frequency": _metric(None, formatter="hz"),
    "/Ac/L3/Energy/Forward": _metric(None, formatter="kwh"),
    "/Ac/L3/Energy/Today": _metric(None, formatter="wh"),
    "/Status": _metric(""),
}

SERVICE_METRICS = {
    **DIRECT_REGISTER_METRICS,
    **DERIVED_SERVICE_METRICS,
}
