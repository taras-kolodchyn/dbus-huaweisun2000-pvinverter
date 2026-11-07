import importlib.util
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / "docker" / "check_telemetry.py"
spec = importlib.util.spec_from_file_location("check_telemetry", HELPER)
telemetry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(telemetry)


def test_accepts_successful_simulator_measurements():
    telemetry.validate_snapshot(
        {
            "/Diagnostics/SuccessCount": 1,
            "/Connected": 1,
            "/Ac/Power": 5800.0,
            "/Dc/Power": 6200.0,
        }
    )


@pytest.mark.parametrize(
    "path,value",
    [
        ("/Diagnostics/SuccessCount", 0),
        ("/Connected", 0),
        ("/Ac/Power", 0),
        ("/Dc/Power", None),
        ("/Ac/Power", float("nan")),
    ],
)
def test_rejects_startup_only_disconnected_or_incorrect_measurements(path, value):
    snapshot = {
        "/Diagnostics/SuccessCount": 1,
        "/Connected": 1,
        "/Ac/Power": 5800,
        "/Dc/Power": 6200,
    }
    snapshot[path] = value
    with pytest.raises(ValueError):
        telemetry.validate_snapshot(snapshot)
