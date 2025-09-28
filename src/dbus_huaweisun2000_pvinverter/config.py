import logging
import os


ENV_LOGLEVEL = "DBUS_HUAWEISUN2000_LOGLEVEL"
DEFAULT_LOGLEVEL = "DEBUG"


def _resolve_log_level(value: str) -> int:
    if value.isdigit():
        return int(value)
    level = logging.getLevelName(value.upper())
    if isinstance(level, int):
        return level
    return logging.getLevelName(DEFAULT_LOGLEVEL)


LOGGING = _resolve_log_level(os.getenv(ENV_LOGLEVEL, DEFAULT_LOGLEVEL))
