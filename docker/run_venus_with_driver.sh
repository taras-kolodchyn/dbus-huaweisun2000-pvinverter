#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT=/workspace
INSTALL_ROOT=/data/dbus-huaweisun2000-pvinverter
USE_INSTALL_SH=${DBUS_HUAWEISUN2000_USE_INSTALL_SH:-0}

SIMULATION=${VENUS_SIMULATION:-a}
SIM_FLAGS=${VENUS_SIMULATION_FLAGS:---with-pvinverter}

SCRIPT_ROOT=/root

driver_root="$WORKSPACE_ROOT"
service_command=(python3 -m dbus_huaweisun2000_pvinverter)
settings_pythonpath=
install_completed=0
SIM_PID=

find_git_dir() {
  local dotgit=$1/.git

  if [ -d "$dotgit" ]; then
    printf '%s\n' "$dotgit"
    return 0
  fi

  if [ -f "$dotgit" ]; then
    sed -n 's/^gitdir: //p' "$dotgit"
    return 0
  fi

  return 1
}

latest_version_tag() {
  local repo_root=$1
  local git_dir

  git_dir=$(find_git_dir "$repo_root") || return 1

  {
    if [ -d "$git_dir/refs/tags" ]; then
      find "$git_dir/refs/tags" -type f | sed "s#^$git_dir/refs/tags/##"
    fi

    if [ -f "$git_dir/packed-refs" ]; then
      awk '
        !/^#/ && !/^\^/ && $2 ~ /^refs\/tags\// {
          sub(/^refs\/tags\//, "", $2)
          print $2
        }
      ' "$git_dir/packed-refs"
    fi
  } | grep -E '^v[0-9]+(\.[0-9]+){2}([-.][0-9A-Za-z]+)*$' | sort -u | sort -V | tail -n1
}

normalize_git_describe() {
  local describe_output=$1

  if [[ "$describe_output" =~ ^v(.+)-([0-9]+)-g[0-9a-f]+$ ]]; then
    printf '%s.post1.dev%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
    return 0
  fi

  if [[ "$describe_output" =~ ^v(.+)$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi

  return 1
}

export_build_version() {
  local version=
  local latest_tag=

  if [ -n "${SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DBUS_HUAWEISUN2000_PVINVERTER:-}" ]; then
    return 0
  fi

  if command -v git >/dev/null 2>&1; then
    version=$(normalize_git_describe "$(git -C "$WORKSPACE_ROOT" describe --tags --match 'v*' 2>/dev/null || true)" || true)
  fi

  if [ -z "$version" ]; then
    latest_tag=$(latest_version_tag "$WORKSPACE_ROOT" || true)
    version=${latest_tag#v}
  fi

  if [ -n "$version" ]; then
    export SETUPTOOLS_SCM_PRETEND_VERSION_FOR_DBUS_HUAWEISUN2000_PVINVERTER="$version"
    echo "INFO: Using SCM version $version for editable install"
  fi
}

pip_install_flags=()
if ! python3 - <<'PY'
import sys

raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
then
  echo "WARNING: venus-docker still exposes $(python3 --version 2>&1); bypassing requires-python for the integration harness" >&2
  pip_install_flags+=(--ignore-requires-python)
fi

if [ "$USE_INSTALL_SH" = "1" ]; then
  rm -rf "$INSTALL_ROOT"
  mkdir -p /data
  cp -a "$WORKSPACE_ROOT/." "$INSTALL_ROOT"
  driver_root="$INSTALL_ROOT"
  service_command=("$INSTALL_ROOT/service/run")
  settings_pythonpath="$INSTALL_ROOT/src"
fi

cd "$driver_root"

if [ -x "$SCRIPT_ROOT/start_services.sh" ]; then
  (cd "$SCRIPT_ROOT" && ./start_services.sh)
else
  echo "WARNING: start_services.sh not available; skipping service startup" >&2
fi

if [ -x "$SCRIPT_ROOT/simulate.sh" ]; then
  (cd "$SCRIPT_ROOT" && ./simulate.sh ${SIM_FLAGS} "${SIMULATION}") &
  SIM_PID=$!
else
  echo "WARNING: simulate.sh not available; skipping simulation playback" >&2
fi

cleanup() {
    if [ "$USE_INSTALL_SH" = "1" ] && [ "$install_completed" = "1" ] && [ -f "$driver_root/uninstall.sh" ]; then
        (cd "$driver_root" && bash uninstall.sh)
        test ! -e /service/dbus-huaweisun2000-pvinverter
    fi

    if [ -n "$SIM_PID" ]; then
        kill "$SIM_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

python3 - <<'PY'
import time
import sys
for _ in range(30):
    try:
        import dbus  # noqa: F401
        dbus.SystemBus()
        break
    except Exception:
        time.sleep(1)
else:
    sys.exit("D-Bus system bus not available")
PY

export_build_version
python3 -m pip install "${pip_install_flags[@]}" -e "$WORKSPACE_ROOT"

installed_version=$(python3 - <<'PY'
from importlib.metadata import version

print(version("dbus-huaweisun2000-pvinverter"))
PY
)
echo "INFO: Editable install resolved version $installed_version"
test "$installed_version" != "0+unknown"

if [ "$USE_INSTALL_SH" = "1" ]; then
  bash install.sh
  test -L /service/dbus-huaweisun2000-pvinverter
  install_completed=1
fi

PYTHONPATH="${settings_pythonpath}${PYTHONPATH:+:$PYTHONPATH}" python3 - <<PY
import os
from dbus.mainloop.glib import DBusGMainLoop
from dbus_huaweisun2000_pvinverter.settings import HuaweiSUN2000Settings

host = os.getenv("DBUS_HUAWEISUN2000_MODBUS_HOST")
port = os.getenv("DBUS_HUAWEISUN2000_MODBUS_PORT")
unit = os.getenv("DBUS_HUAWEISUN2000_MODBUS_UNIT")

if any([host, port, unit]):
    DBusGMainLoop(set_as_default=True)
    settings = HuaweiSUN2000Settings()
    if host:
        settings.set("modbus_host", host)
    if port:
        settings.set("modbus_port", int(port))
    if unit:
        settings.set("modbus_unit", int(unit))
PY

if [ "$USE_INSTALL_SH" = "1" ]; then
  "${service_command[@]}" >/tmp/dbus-huaweisun2000-service.log 2>&1
  grep -q "Connected to dbus" /tmp/dbus-huaweisun2000-service.log
  grep -q "Oneshot mode active" /tmp/dbus-huaweisun2000-service.log
else
  exec "${service_command[@]}"
fi
