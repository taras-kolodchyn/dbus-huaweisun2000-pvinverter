"""Huawei SUN2000 D-Bus PV inverter integration."""

from importlib.metadata import PackageNotFoundError, version as package_version
from typing import Any

try:
    __version__ = package_version("dbus-huaweisun2000-pvinverter")
except PackageNotFoundError:
    __version__ = "0+unknown"


def main(*args: Any, **kwargs: Any):
    """Lazy-import the CLI entry point to avoid hard dependencies at import time."""

    from .main import main as _main

    return _main(*args, **kwargs)


__all__ = ["__version__", "main"]
