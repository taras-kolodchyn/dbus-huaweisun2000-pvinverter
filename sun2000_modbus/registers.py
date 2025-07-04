from enum import Enum

from . import datatypes
from . import mappings


class AccessType(Enum):
    RO = "ro"
    RW = "rw"
    WO = "wo"


class Register:
    address: int
    quantity: int
    data_type: datatypes.DataType
    gain: float
    unit: str
    access_type: AccessType
    mapping: dict

    def __init__(
        self,
        address,
        quantity,
        data_type,
        gain,
        unit,
        access_type,
        mapping,
    ):
        self.address = address
        self.quantity = quantity
        self.data_type = data_type
        self.gain = gain
        self.unit = unit
        self.access_type = access_type
        self.mapping = mapping


class InverterEquipmentRegister(Enum):
    Model = Register(
        30000, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    HardwareVersion = Register(
        31000, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    SN = Register(30015, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None)
    PN = Register(30025, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None)
    ModelID = Register(
        30070, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    ProtocolVersion = Register(
        30068, 2, datatypes.DataType.UINT32_BE, None, None, AccessType.RO, None
    )
    SoftwareVersion = Register(
        30050, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    FirmwareVersion = Register(
        30035, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    NumberOfPVStrings = Register(
        30071, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    NumberOfMPPTrackers = Register(
        30072, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    RatedPower = Register(
        30073, 2, datatypes.DataType.UINT32_BE, 1, "W", AccessType.RO, None
    )
    MaximumActivePower = Register(
        30075, 2, datatypes.DataType.UINT32_BE, 1, "W", AccessType.RO, None
    )
    MaximumApparentPower = Register(
        30077, 2, datatypes.DataType.UINT32_BE, 1000, "kVA", AccessType.RO, None
    )
    MaximumReactivePowerFedToTheGrid = Register(
        30079, 2, datatypes.DataType.INT32_BE, 1000, "kvar", AccessType.RO, None
    )
    MaximumReactivePowerAbsorbedFromTheGrid = Register(
        30081, 2, datatypes.DataType.INT32_BE, 1000, "kvar", AccessType.RO, None
    )
    State1 = Register(
        32000, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None
    )
    State2 = Register(
        32002, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None
    )
    State3 = Register(
        32003, 2, datatypes.DataType.BITFIELD32, None, None, AccessType.RO, None
    )
    Alarm1 = Register(
        32008, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None
    )
    Alarm2 = Register(
        32009, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None
    )
    Alarm3 = Register(
        32010, 1, datatypes.DataType.BITFIELD16, None, None, AccessType.RO, None
    )
    PV1Voltage = Register(
        32016, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV1Current = Register(
        32017, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV2Voltage = Register(
        32018, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV2Current = Register(
        32019, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV3Voltage = Register(
        32020, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV3Current = Register(
        32021, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV4Voltage = Register(
        32022, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV4Current = Register(
        32023, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV5Voltage = Register(
        32024, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV5Current = Register(
        32025, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV6Voltage = Register(
        32026, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV6Current = Register(
        32027, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV7Voltage = Register(
        32028, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV7Current = Register(
        32029, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV8Voltage = Register(
        32030, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV8Current = Register(
        32031, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV9Voltage = Register(
        32032, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV9Current = Register(
        32033, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV10Voltage = Register(
        32034, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV10Current = Register(
        32035, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV11Voltage = Register(
        32036, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV11Current = Register(
        32037, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV12Voltage = Register(
        32038, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV12Current = Register(
        32039, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV13Voltage = Register(
        32040, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV13Current = Register(
        32041, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV14Voltage = Register(
        32042, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV14Current = Register(
        32043, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV15Voltage = Register(
        32044, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV15Current = Register(
        32045, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV16Voltage = Register(
        32046, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV16Current = Register(
        32047, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV17Voltage = Register(
        32048, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV17Current = Register(
        32049, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV18Voltage = Register(
        32050, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV18Current = Register(
        32051, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV19Voltage = Register(
        32052, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV19Current = Register(
        32053, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV20Voltage = Register(
        32054, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV20Current = Register(
        32055, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV21Voltage = Register(
        32056, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV21Current = Register(
        32057, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV22Voltage = Register(
        32058, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV22Current = Register(
        32059, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV23Voltage = Register(
        32060, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV23Current = Register(
        32061, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    PV24Voltage = Register(
        32062, 1, datatypes.DataType.INT16_BE, 10, "V", AccessType.RO, None
    )
    PV24Current = Register(
        32063, 1, datatypes.DataType.INT16_BE, 100, "A", AccessType.RO, None
    )
    InputPower = Register(
        32064, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    LineVoltageBetweenPhasesAAndB = Register(
        32066, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    LineVoltageBetweenPhasesBAndC = Register(
        32067, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    LineVoltageBetweenPhasesCAndA = Register(
        32068, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    PhaseAVoltage = Register(
        32069, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    PhaseBVoltage = Register(
        32070, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    PhaseCVoltage = Register(
        32071, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    PhaseACurrent = Register(
        32072, 2, datatypes.DataType.INT32_BE, 1000, "A", AccessType.RO, None
    )
    PhaseBCurrent = Register(
        32074, 2, datatypes.DataType.INT32_BE, 1000, "A", AccessType.RO, None
    )
    PhaseCCurrent = Register(
        32076, 2, datatypes.DataType.INT32_BE, 1000, "A", AccessType.RO, None
    )
    PeakActivePowerOfCurrentDay = Register(
        32078, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    ActivePower = Register(
        32080, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    ReactivePower = Register(
        32082, 2, datatypes.DataType.INT32_BE, 1000, "kvar", AccessType.RO, None
    )
    PowerFactor = Register(
        32084, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RO, None
    )
    GridFrequency = Register(
        32085, 1, datatypes.DataType.UINT16_BE, 100, "Hz", AccessType.RO, None
    )
    Efficiency = Register(
        32086, 1, datatypes.DataType.UINT16_BE, 100, "%", AccessType.RO, None
    )
    InternalTemperature = Register(
        32087, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )
    InsulationResistance = Register(
        32088, 1, datatypes.DataType.UINT16_BE, 1000, "MOhm", AccessType.RO, None
    )
    DeviceStatus = Register(
        32089,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RO,
        mappings.DeviceStatus,
    )
    FaultCode = Register(
        32090, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    StartupTime = Register(
        32091, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RO, None
    )
    ShutdownTime = Register(
        32093, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RO, None
    )
    AccumulatedEnergyYield = Register(
        32106, 2, datatypes.DataType.UINT32_BE, 100, "kWh", AccessType.RO, None
    )
    DailyEnergyYield = Register(
        32114, 2, datatypes.DataType.UINT32_BE, 100, "kWh", AccessType.RO, None
    )
    ActiveAdjustmentMode = Register(
        35300, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    ActiveAdjustmentValue = Register(
        35302, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RO, None
    )
    ActiveAdjustmentCommand = Register(
        35303, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    ReactiveAdjustmentMode = Register(
        35304, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    ReactiveAdjustmentValue = Register(
        35305, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RO, None
    )
    ReactiveAdjustmentCommand = Register(
        35307, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    PowerMeterCollectionActivePower = Register(
        37113, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    TotalNumberOfOptimizers = Register(
        37200, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    NumberOfOnlineOptimizers = Register(
        37201, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    FeatureData = Register(
        37202, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    SystemTime = Register(
        40000, 2, datatypes.DataType.UINT32_BE, 1, None, AccessType.RW, None
    )
    QUCharacteristicCurveMode = Register(
        40037, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    QUDispatchTriggerPower = Register(
        40038, 1, datatypes.DataType.UINT16_BE, 1, "%", AccessType.RW, None
    )
    FixedActivePowerDeratedInKW = Register(
        40120, 1, datatypes.DataType.UINT16_BE, 10, "kW", AccessType.RW, None
    )
    ReactivePowerCompensationInPF = Register(
        40122, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RW, None
    )
    ReactivePowerCompensationQS = Register(
        40123, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RW, None
    )
    ActivePowerPercentageDerating = Register(
        40125, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RW, None
    )
    FixedActivePowerDeratedInW = Register(
        40126, 2, datatypes.DataType.UINT32_BE, 1, "W", AccessType.RW, None
    )
    ReactivePowerCompensationAtNight = Register(
        40129, 2, datatypes.DataType.INT32_BE, 1000, "kvar", AccessType.RW, None
    )
    CosPhiPPnCharacteristicCurve = Register(
        40133, 21, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None
    )
    QUCharacteristicCurve = Register(
        40154, 21, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None
    )
    PFUCharacteristicCurve = Register(
        40175, 21, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None
    )
    ReactivePowerAdjustmentTime = Register(
        40196, 1, datatypes.DataType.UINT16_BE, 1, "s", AccessType.RW, None
    )
    QUPowerPercentageToExitScheduling = Register(
        40198, 1, datatypes.DataType.UINT16_BE, 1, "%", AccessType.RW, None
    )
    Startup = Register(
        40200, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.WO, None
    )
    Shutdown = Register(
        40201, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.WO, None
    )
    GridCode = Register(
        42000, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    ReactivePowerChangeGradient = Register(
        42015, 2, datatypes.DataType.UINT32_BE, 1000, "%/s", AccessType.RW, None
    )
    ActivePowerChangeGradient = Register(
        42017, 2, datatypes.DataType.UINT32_BE, 1000, "%/s", AccessType.RW, None
    )
    ScheduleInstructionValidDuration = Register(
        42019, 2, datatypes.DataType.UINT32_BE, 1, "s", AccessType.RW, None
    )
    TimeZone = Register(
        43006, 1, datatypes.DataType.INT16_BE, 1, "min", AccessType.RW, None
    )


class BatteryEquipmentRegister(Enum):
    # Overall
    RunningStatus = Register(
        37762,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RO,
        mappings.RunningStatus,
    )
    WorkingModeSettings = Register(
        47086,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.WorkingModeSettings,
    )
    BusVoltage = Register(
        37763, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    BusCurrent = Register(
        37764, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    ChargeDischargePower = Register(
        37765, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    MaximumChargePower = Register(
        37046, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    MaximumDischargePower = Register(
        37048, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    RatedCapacity = Register(
        37758, 2, datatypes.DataType.INT32_BE, 1, "Wh", AccessType.RO, None
    )
    SOC = Register(37760, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None)
    BackupPowerSOC = Register(
        47102, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RW, None
    )
    TotalCharge = Register(
        37780, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    TotalDischarge = Register(
        37782, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    CurrentDayChargeCapacity = Register(
        37784, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    CurrentDayDischargeCapacity = Register(
        37786, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    TimeOfUseElectricityPricePeriods = Register(
        47028, 41, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None
    )
    MaximumChargingPower = Register(
        47075, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RW, None
    )
    MaximumDischargingPower = Register(
        47077, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RW, None
    )
    ChargingCutoffCapacity = Register(
        47081, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RW, None
    )
    DischargeCutoffCapacity = Register(
        47082, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RW, None
    )
    ForcedChargingAndDischargingPeriod = Register(
        47083, 1, datatypes.DataType.UINT16_BE, 1, "minutes", AccessType.RW, None
    )
    ChargeFromGridFunction = Register(
        47087,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.ChargeFromGridFunction,
    )
    GridChargeCutoffSOC = Register(
        47088, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RW, None
    )
    # ForcibleChargeDischarge = Register(
    #     47100,
    #     1,
    #     datatypes.DataType.UINT16_BE,
    #     1,
    #     None,
    #     AccessType.WO,
    #     mappings.ForcibleChargeDischarge,
    # )  # disabled because not readable (AccessType.WO)
    FixedChargingAndDischargingPeriods = Register(
        47200, 41, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None
    )
    PowerOfChargeFromGrid = Register(
        47242, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RW, None
    )
    MaximumPowerOfChargeFromGrid = Register(
        47244, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RW, None
    )
    ForcibleChargeDischargeSettingMode = Register(
        47246,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.ForcibleChargeDischargeSettingMode,
    )
    ForcibleChargePower = Register(
        47247, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RW, None
    )
    ForcibleDischargePower = Register(
        47249, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RW, None
    )
    TimeOfUseChargingAndDischargingPeriods = Register(
        47255, 43, datatypes.DataType.MULTIDATA, None, None, AccessType.RW, None
    )
    ExcessPVEnergyUseInTOU = Register(
        47299,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.ExcessPVEnergyUseInTOU,
    )
    ActivePowerControlMode = Register(
        47415,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.ActivePowerControlMode,
    )
    MaximumFeedGridPowerInKW = Register(
        47416, 2, datatypes.DataType.INT32_BE, 1000, "kW", AccessType.RW, None
    )
    MaximumFeedGridPowerInPercentage = Register(
        47418, 1, datatypes.DataType.INT16_BE, 10, "%", AccessType.RW, None
    )
    MaximumChargeFromGridPower = Register(
        47590, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RW, None
    )
    SwitchToOffGrid = Register(
        47604,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.SwitchToOffGrid,
    )
    VoltageInIndependentOperation = Register(
        47605,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.VoltageIndependentOperation,
    )

    # Unit 1
    Unit1ProductModel = Register(
        47000,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.ProductModel,
    )
    Unit1SN = Register(
        37052, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1No = Register(
        47107, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    Unit1SoftwareVersion = Register(
        37814, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1DCDCVersion = Register(
        37026, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1BMSVersion = Register(
        37036, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1RunningStatus = Register(
        37000,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RO,
        mappings.RunningStatus,
    )
    Unit1WorkingMode = Register(
        37006,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RO,
        mappings.WorkingMode,
    )
    Unit1BusVoltage = Register(
        37003, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    Unit1BusCurrent = Register(
        37021, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    Unit1BatterySOC = Register(
        37004, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None
    )
    Unit1ChargeAndDischargePower = Register(
        37001, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    Unit1RemainingChargeDischargeTime = Register(
        37025, 1, datatypes.DataType.UINT16_BE, 1, "minutes", AccessType.RO, None
    )
    Unit1RatedChargePower = Register(
        37007, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    Unit1RatedDischargePower = Register(
        37009, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    Unit1CurrentDayChargeCapacity = Register(
        37015, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1CurrentDayDischargeCapacity = Register(
        37017, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1TotalCharge = Register(
        37066, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1TotalDischarge = Register(
        37068, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1BatteryTemperature = Register(
        37022, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )
    Unit1FaultID = Register(
        37014, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )

    # Unit 2
    Unit2ProductModel = Register(
        47089,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RW,
        mappings.ProductModel,
    )
    Unit2SN = Register(
        37700, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit2No = Register(
        47108, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    Unit2SoftwareVersion = Register(
        37799, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit2RunningStatus = Register(
        37741,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RO,
        mappings.RunningStatus,
    )
    Unit2BusVoltage = Register(
        37750, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    Unit2BusCurrent = Register(
        37751, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    Unit2BatterySOC = Register(
        37738, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None
    )
    Unit2ChargeAndDischargePower = Register(
        37743, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    Unit2CurrentDayChargeCapacity = Register(
        37746, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2CurrentDayDischargeCapacity = Register(
        37748, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2TotalCharge = Register(
        37753, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2TotalDischarge = Register(
        37755, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2BatteryTemperature = Register(
        37752, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )

    # Unit 1 BatteryPack 1
    Unit1BatteryPack1SN = Register(
        38200, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1BatteryPack1No = Register(
        47750, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    Unit1BatteryPack1FirmwareVersion = Register(
        38210, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1BatteryPack1WorkingStatus = Register(
        38228, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    Unit1BatteryPack1Voltage = Register(
        38235, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    Unit1BatteryPack1Current = Register(
        38236, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    Unit1BatteryPack1SOC = Register(
        38229, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None
    )
    Unit1BatteryPack1ChargeDischargePower = Register(
        38233, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RO, None
    )
    Unit1BatteryPack1TotalCharge = Register(
        38238, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1BatteryPack1TotalDischarge = Register(
        38240, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1BatteryPack1MinimumTemperature = Register(
        38453, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )
    Unit1BatteryPack1MaximumTemperature = Register(
        38452, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )

    # Unit 1 BatteryPack 2
    Unit1BatteryPack2SN = Register(
        38242, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1BatteryPack2No = Register(
        47751, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    Unit1BatteryPack2FirmwareVersion = Register(
        38252, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1BatteryPack2WorkingStatus = Register(
        38270, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    Unit1BatteryPack2Voltage = Register(
        38277, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    Unit1BatteryPack2Current = Register(
        38278, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    Unit1BatteryPack2SOC = Register(
        38271, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None
    )
    Unit1BatteryPack2ChargeDischargePower = Register(
        38275, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RO, None
    )
    Unit1BatteryPack2TotalCharge = Register(
        38280, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1BatteryPack2TotalDischarge = Register(
        38282, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1BatteryPack2MinimumTemperature = Register(
        38455, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )
    Unit1BatteryPack2MaximumTemperature = Register(
        38454, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )

    # Unit 1 BatteryPack 3
    Unit1BatteryPack3SN = Register(
        38284, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1BatteryPack3No = Register(
        47752, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    Unit1BatteryPack3FirmwareVersion = Register(
        38294, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit1BatteryPack3WorkingStatus = Register(
        38312, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    Unit1BatteryPack3Voltage = Register(
        38319, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    Unit1BatteryPack3Current = Register(
        38320, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    Unit1BatteryPack3SOC = Register(
        38313, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None
    )
    Unit1BatteryPack3ChargeDischargePower = Register(
        38317, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RO, None
    )
    Unit1BatteryPack3TotalCharge = Register(
        38322, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1BatteryPack3TotalDischarge = Register(
        38324, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit1BatteryPack3MinimumTemperature = Register(
        38457, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )
    Unit1BatteryPack3MaximumTemperature = Register(
        38456, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )

    # Unit 2 BatteryPack 1
    Unit2BatteryPack1SN = Register(
        38326, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit2BatteryPack1No = Register(
        47753, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    Unit2BatteryPack1FirmwareVersion = Register(
        38336, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit2BatteryPack1WorkingStatus = Register(
        38354, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    Unit2BatteryPack1Voltage = Register(
        38361, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    Unit2BatteryPack1Current = Register(
        38362, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    Unit2BatteryPack1SOC = Register(
        38355, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None
    )
    Unit2BatteryPack1ChargeDischargePower = Register(
        38359, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RO, None
    )
    Unit2BatteryPack1TotalCharge = Register(
        38364, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2BatteryPack1TotalDischarge = Register(
        38366, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2BatteryPack1MinimumTemperature = Register(
        38459, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )
    Unit2BatteryPack1MaximumTemperature = Register(
        38458, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )

    # Unit 2 BatteryPack 2
    Unit2BatteryPack2SN = Register(
        38368, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit2BatteryPack2No = Register(
        47754, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    Unit2BatteryPack2FirmwareVersion = Register(
        38378, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit2BatteryPack2WorkingStatus = Register(
        38396, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    Unit2BatteryPack2Voltage = Register(
        38403, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    Unit2BatteryPack2Current = Register(
        38404, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    Unit2BatteryPack2SOC = Register(
        38397, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None
    )
    Unit2BatteryPack2ChargeDischargePower = Register(
        38401, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RO, None
    )
    Unit2BatteryPack2TotalCharge = Register(
        38406, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2BatteryPack2TotalDischarge = Register(
        38408, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2BatteryPack2MinimumTemperature = Register(
        38461, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )
    Unit2BatteryPack2MaximumTemperature = Register(
        38460, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )

    # Unit 2 BatteryPack 3
    Unit2BatteryPack3SN = Register(
        38410, 10, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit2BatteryPack3No = Register(
        47755, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RW, None
    )
    Unit2BatteryPack3FirmwareVersion = Register(
        38420, 15, datatypes.DataType.STRING, None, None, AccessType.RO, None
    )
    Unit2BatteryPack3WorkingStatus = Register(
        38438, 1, datatypes.DataType.UINT16_BE, 1, None, AccessType.RO, None
    )
    Unit2BatteryPack3Voltage = Register(
        38445, 1, datatypes.DataType.UINT16_BE, 10, "V", AccessType.RO, None
    )
    Unit2BatteryPack3Current = Register(
        38446, 1, datatypes.DataType.INT16_BE, 10, "A", AccessType.RO, None
    )
    Unit2BatteryPack3SOC = Register(
        38439, 1, datatypes.DataType.UINT16_BE, 10, "%", AccessType.RO, None
    )
    Unit2BatteryPack3ChargeDischargePower = Register(
        38443, 2, datatypes.DataType.INT32_BE, 0.1, "W", AccessType.RO, None
    )
    Unit2BatteryPack3TotalCharge = Register(
        38448, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2BatteryPack3TotalDischarge = Register(
        38450, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    Unit2BatteryPack3MinimumTemperature = Register(
        38463, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )
    Unit2BatteryPack3MaximumTemperature = Register(
        38462, 1, datatypes.DataType.INT16_BE, 10, "°C", AccessType.RO, None
    )


class MeterEquipmentRegister(Enum):
    MeterType = Register(
        37125,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RO,
        mappings.MeterType,
    )
    MeterStatus = Register(
        37100,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RO,
        mappings.MeterStatus,
    )
    MeterModelDetectionResult = Register(
        37138,
        1,
        datatypes.DataType.UINT16_BE,
        1,
        None,
        AccessType.RO,
        mappings.MeterModelDetectionResult,
    )
    APhaseVoltage = Register(
        37101, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None
    )
    BPhaseVoltage = Register(
        37103, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None
    )
    CPhaseVoltage = Register(
        37105, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None
    )
    APhaseCurrent = Register(
        37107, 2, datatypes.DataType.INT32_BE, 100, "A", AccessType.RO, None
    )
    BPhaseCurrent = Register(
        37109, 2, datatypes.DataType.INT32_BE, 100, "A", AccessType.RO, None
    )
    CPhaseCurrent = Register(
        37111, 2, datatypes.DataType.INT32_BE, 100, "A", AccessType.RO, None
    )
    ActivePower = Register(
        37113, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    ReactivePower = Register(
        37115, 2, datatypes.DataType.INT32_BE, 1, "var", AccessType.RO, None
    )
    PowerFactor = Register(
        37117, 1, datatypes.DataType.INT16_BE, 1000, None, AccessType.RO, None
    )
    GridFrequency = Register(
        37118, 1, datatypes.DataType.INT16_BE, 100, "Hz", AccessType.RO, None
    )
    PositiveActiveElectricity = Register(
        37119, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    ReverseActivePower = Register(
        37121, 2, datatypes.DataType.INT32_BE, 100, "kWh", AccessType.RO, None
    )
    AccumulatedReactivePower = Register(
        37123, 2, datatypes.DataType.INT32_BE, 100, "kvar", AccessType.RO, None
    )
    ABLineVoltage = Register(
        37126, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None
    )
    BCLineVoltage = Register(
        37128, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None
    )
    CALineVoltage = Register(
        37130, 2, datatypes.DataType.INT32_BE, 10, "V", AccessType.RO, None
    )
    APhaseActivePower = Register(
        37132, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    BPhaseActivePower = Register(
        37134, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
    CPhaseActivePower = Register(
        37136, 2, datatypes.DataType.INT32_BE, 1, "W", AccessType.RO, None
    )
