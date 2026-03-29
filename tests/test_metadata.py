import pathlib
import sys
import tomllib

SRC_DIR = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from dbus_huaweisun2000_pvinverter import __version__  # noqa: E402
from dbus_huaweisun2000_pvinverter.sun2000_modbus import (  # noqa: E402
    __version__ as modbus_version,
)


def test_package_versions_are_exposed_consistently():
    assert __version__
    assert modbus_version == __version__


def test_pyproject_uses_setuptools_scm_for_versioning():
    pyproject_path = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text())

    assert pyproject["project"]["requires-python"] == ">=3.12"
    assert "version" not in pyproject["project"]
    assert pyproject["project"]["dynamic"] == ["version"]
    assert "setuptools-scm>=8" in pyproject["build-system"]["requires"]
    assert pyproject["tool"]["setuptools_scm"]["tag_regex"] == "^v(?P<version>.+)$"


def test_readme_release_download_matches_workflow_asset_name():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text()
    workflow = (repo_root / ".github" / "workflows" / "python-ci.yml").read_text()

    latest_download = "releases/latest/download/dbus-huaweisun2000-pvinverter.zip"
    assert latest_download in readme
    assert "dbus-huaweisun2000-pvinverter.zip" in workflow
    assert "python-3.12-blue.svg" in readme
    assert "python-version: '3.12'" in workflow
    assert "Venus OS (**v3.71+**)" in readme
    assert "below v3.71 is not supported" in readme
    assert "This project now targets **GUI-v2 only**." in readme
    assert "Browser Remote Console note" not in readme
    assert "Classic UI" not in readme
    assert not (repo_root / "gui-v2").exists()
    assert not (repo_root / "patches" / "gui-v2").exists()


def test_venus_docker_harness_exports_version_for_editable_installs():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    harness = (repo_root / "docker" / "run_venus_with_driver.sh").read_text()

    assert "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DBUS_HUAWEISUN2000_PVINVERTER" in harness
    assert "--ignore-requires-python" in harness
    assert 'test "$installed_version" != "0+unknown"' in harness
