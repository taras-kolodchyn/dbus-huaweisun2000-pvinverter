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
