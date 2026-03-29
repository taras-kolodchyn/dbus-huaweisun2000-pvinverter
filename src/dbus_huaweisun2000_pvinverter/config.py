import logging
import os

ENV_LOGLEVEL = "DBUS_HUAWEISUN2000_LOGLEVEL"
DEFAULT_LOGLEVEL = "INFO"
DEFAULT_MODBUS_HOST = "255.255.255.255"
DEFAULT_MODBUS_PORT = 502
DEFAULT_MODBUS_UNIT = 0
DEFAULT_PHASE_TYPE_OVERRIDE = "Auto"
DEFAULT_CUSTOM_NAME = "Huawei SUN2000"
DEFAULT_POSITION = 0
DEFAULT_UPDATE_TIME_MS = 3000
DEFAULT_POWER_CORRECTION_FACTOR = 0.995
UNCONFIGURED_MODBUS_HOSTS = {"", "0.0.0.0", DEFAULT_MODBUS_HOST}


def _resolve_log_level(value: str) -> int:
    if value.isdigit():
        return int(value)
    level = logging.getLevelName(value.upper())
    if isinstance(level, int):
        return level
    return logging.getLevelName(DEFAULT_LOGLEVEL)


LOGGING = _resolve_log_level(os.getenv(ENV_LOGLEVEL, DEFAULT_LOGLEVEL))
