"""Huawei SUN2000 D-Bus PV inverter integration."""

from typing import Any


def main(*args: Any, **kwargs: Any):
    """Lazy-import the CLI entry point to avoid hard dependencies at import time."""

    from .main import main as _main

    return _main(*args, **kwargs)


__all__ = ["main"]
