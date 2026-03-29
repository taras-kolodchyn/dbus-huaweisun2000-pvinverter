# dbus-huaweisun2000-pvinverter

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/taras-kolodchyn/dbus-huaweisun2000-pvinverter)](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/releases)
![Platform](https://img.shields.io/badge/platform-Venus%20OS%20(Cerbo%20GX)-informational)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Build Status](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/actions/workflows/python-ci.yml/badge.svg?branch=main)](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/actions/workflows/python-ci.yml)
![Last Commit](https://img.shields.io/github/last-commit/taras-kolodchyn/dbus-huaweisun2000-pvinverter)
![Commit Activity](https://img.shields.io/github/commit-activity/m/taras-kolodchyn/dbus-huaweisun2000-pvinverter)
![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)
![GitHub all releases](https://img.shields.io/github/downloads/taras-kolodchyn/dbus-huaweisun2000-pvinverter/total)
![GitHub issues](https://img.shields.io/github/issues/taras-kolodchyn/dbus-huaweisun2000-pvinverter)
![GitHub pull requests](https://img.shields.io/github/issues-pr/taras-kolodchyn/dbus-huaweisun2000-pvinverter)

> **A D-Bus driver for seamless integration of Huawei SUN2000 inverters into Victron Cerbo GX / Venus OS**

---

## 🚀 Overview

`dbus-huaweisun2000-pvinverter` brings live data from Huawei SUN2000 PV inverters directly into your Victron Venus OS (Cerbo GX) and VRM Portal — no additional hardware required.  
Get detailed monitoring, energy analytics, and remote diagnostics — all in one open-source, easy-to-install package.

---

## ⚡ Features

- **Live monitoring:** All key metrics from your Huawei inverter in Venus OS & VRM.
- **Zero hardware hacks:** Works over Modbus TCP (WiFi/LAN).
- **Easy integration:** Clean D-Bus API for use with Victron native apps.
- **Simple install/update/uninstall scripts.**
- **Auto reconnection & robust error handling.**
- **Fully open source — contribute and extend!**

---

## 📦 Requirements

- **Victron Cerbo GX** or compatible device with Venus OS (**v3.71+**)
- **Huawei SUN2000 inverter** (any recent model)
- **Inverter WiFi or LAN access** (Modbus TCP port 502 open)
- **Python 3.12** runtime on current Venus OS releases

> ⚠️ **Venus OS firmware below v3.71 is not supported.** Earlier releases ship an older
> Python runtime and will not run this version of the driver.

---

## 🧪 Tested Devices & Compatibility

| Device           | Version                       | Status         |
|------------------|-------------------------------|----------------|
| Cerbo GX         | Venus OS v3.71 and newer      | Supported      |
| SUN2000-30KTL-M3 | Latest firmware               | Supported      |

- Venus OS versions before v3.71 are not supported by the current Python 3.12 baseline.
- Other recent Huawei SUN2000 inverters should work if they support Modbus TCP.
- See [Issues](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/issues) for compatibility reports.

---

## 📥 Installation

### 1. Download and deploy

**From GitHub Releases (recommended for stable):**

```bash
cd /data
wget https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/releases/latest/download/dbus-huaweisun2000-pvinverter.zip -O dbus-huaweisun2000-pvinverter.zip || \
  wget https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/releases/download/v1.1.0/dbus-huaweisun2000-pvinverter-v1.1.0.zip -O dbus-huaweisun2000-pvinverter.zip
unzip dbus-huaweisun2000-pvinverter.zip -d dbus-huaweisun2000-pvinverter
cd dbus-huaweisun2000-pvinverter
chmod +x install.sh
sh install.sh
```

**Or clone the latest main branch (for advanced users):**

```bash
scp -r dbus-huaweisun2000-pvinverter root@venus:/data/
# or
cd /data
wget https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/archive/refs/heads/main.zip
unzip main.zip -d dbus-huaweisun2000-pvinverter
mv dbus-huaweisun2000-pvinverter-main dbus-huaweisun2000-pvinverter
chmod +x dbus-huaweisun2000-pvinverter/install.sh
sh dbus-huaweisun2000-pvinverter/install.sh
```

---

## ▶️ Usage

- Service autostarts after installation.
- Fresh installs stay idle until you set a real inverter IP instead of the default
  `255.255.255.255`.
- **Check status:** `svstat /service/dbus-huaweisun2000-pvinverter`
- **Manual debug:**  
  `PYTHONPATH=/data/dbus-huaweisun2000-pvinverter/src python -m dbus_huaweisun2000_pvinverter`
- **Logs:**  
  `tail -f /var/log/dbus-huaweisun2000/current | tai64nlocal`

## ⚙️ Configuration

This project now targets **GUI-v2 only**.

- Configure the driver directly on Venus OS with:
  ```bash
  sh /data/dbus-huaweisun2000-pvinverter/configure.sh --host 192.168.211.50 --port 502 --unit 3
  sh /data/dbus-huaweisun2000-pvinverter/configure.sh --position 2 --custom-name "Huawei SUN2000"
  sh /data/dbus-huaweisun2000-pvinverter/configure.sh --vrm-instance 20
  sh /data/dbus-huaweisun2000-pvinverter/configure.sh --show
  ```
- The script writes settings under `com.victronenergy.settings`, so changes survive restarts.
- If you prefer manual editing, use Remote Console → `dbus-spy` and update `/Settings/HuaweiSUN2000/*`.

---

## 🔄 Updating

```bash
sh /data/dbus-huaweisun2000-pvinverter/restart.sh
```

---

## 🗑️ Uninstall

```bash
sh /data/dbus-huaweisun2000-pvinverter/uninstall.sh
rm -r /data/dbus-huaweisun2000-pvinverter/
```

---

## 📸 Screenshots

### New UI (Venus OS)

![New UI Main Overview](img/new-ui/main-ui-1.png)  
![New UI Details](img/new-ui/main-ui-2.png)  
![New UI Settings](img/new-ui/main-ui-3.png)  

### VRM Portal

![VRM Portal Main Page](img/vrm/vrm-01.png)  
![VRM Portal Devices Page](img/vrm/vrm-02.png)  

---

## 💡 Troubleshooting

- **No data in VRM?**  
  Check Modbus settings (IP, port 502, unit ID), network, and logs.
- **Service restarts?**  
  Run main script manually and watch logs for errors.
- **General logs:**  
  `tail -f /var/log/dbus-huaweisun2000/current | tai64nlocal`
- See [GitHub Issues](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/issues) or [Discussions](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/discussions).

---

## ⚙️ Configuration

- **Runtime log level** — override the default `DEBUG` output by exporting
  `DBUS_HUAWEISUN2000_LOGLEVEL` (e.g. `INFO`, `WARNING`, or a numeric level) before
  launching the service.
- **Power correction factor** — continue to use the GUI/D-Bus setting so the factor
  persists across restarts.
- **Modbus override (dev mode)** — set `DBUS_HUAWEISUN2000_MODBUS_HOST`,
  `DBUS_HUAWEISUN2000_MODBUS_PORT`, or `DBUS_HUAWEISUN2000_MODBUS_UNIT` to point the
  driver at a simulator such as the Docker Compose stack described below. Runtime
  defaults are host `255.255.255.255`, port `502`, and unit `0`.
- **Phase type override** — if your inverter model naming is unusual, set
  `DBUS_HUAWEISUN2000_PHASE_TYPE` to `single-phase` or `three-phase` to override auto
  detection.

---

## 🛠 Development

### Project layout

- `src/dbus_huaweisun2000_pvinverter/` — packaged Python source (service entry point, Modbus logic).
- `tests/` — self-contained unit tests using lightweight stubs for system dependencies.
- `service/` — run scripts used by the Venus OS init system.
- `img/` — screenshots bundled with releases.

### Local workflow

1. Install tooling and dependencies:
   ```bash
   python3.12 -m pip install --upgrade pip
   python3.12 -m pip install '.[dev]'
   ```
2. Run quality checks locally:
   ```bash
   black --check .
   flake8 .
   pytest --maxfail=1 --disable-warnings -q
   bash docker/test_install_uninstall.sh
   ```
3. Reproduce the GitHub Actions pipeline with [act](https://github.com/nektos/act):
   ```bash
   act -j ci
   # On Apple silicon you may need:
   act -j ci --container-architecture linux/amd64
   ```
   Make sure Docker is running and `act` is installed.
4. See [CONTRIBUTING.md](CONTRIBUTING.md) for additional guidelines.

### Docker playground

Launch a fully-contained simulator (based on `victronenergy/venus-docker` and a simple
Modbus mock) with Docker Compose:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Run the heavier install/runtime/uninstall integration check with:

```bash
docker compose -f docker-compose.dev.yml -f docker-compose.install-test.yml up --build --abort-on-container-exit
docker compose -f docker-compose.dev.yml -f docker-compose.install-test.yml down --volumes --remove-orphans
```

The stack pulls the official Venus OS development image, installs this driver in editable
mode, starts a lightweight Modbus simulator, and runs the service in "oneshot" mode against
the simulated registers. Use `CTRL+C` (or `docker compose down --volumes --remove-orphans`)
to stop the containers. Edit the code on your host and re-run the command – the Venus
container reinstalls the project on every start so changes are reflected immediately. When
the image does not have the `git` CLI available, the harness still resolves a best-effort
package version from repository tags so editable installs do not fall back to `0+unknown`.

Environment knobs:

- `VENUS_SIMULATION` (default `a`) selects the mock system loaded by `simulate.sh`.
- `VENUS_SIMULATION_FLAGS` (default `--with-pvinverter`) forwards extra devices to the
  simulation.
- `DBUS_HUAWEISUN2000_MODBUS_*` override the Modbus endpoint that the driver connects to
  (by default the bundled simulator). The playground pins the simulator to Modbus unit
  `1` explicitly, while the real driver default remains `0` until configured.

---

## 📝 License

MIT License. See [LICENSE](LICENSE).

---

## ☕ Support

If you find this project useful and want to support its development, you can help in the following ways:

- **Star the repository** ⭐ — It helps others discover the project.  
- **Report bugs or request features** via [GitHub Issues](../../issues).  
- **Join discussions** in the [GitHub Discussions](../../discussions).  
- **Contribute code** — See the [Contributing](#-contributing) section.  

---

### 💖 Direct Support

[![Buy Me a Coffee](https://img.shields.io/badge/☕_Buy_Me_a_Coffee-FE8133?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/taras.kolodchyn)
[![Support via PrivatBank](https://img.shields.io/badge/🇺🇦_Support-via_PrivatBank-0057B7?style=for-the-badge&labelColor=FFD700&logo=paypal&logoColor=white)](https://www.privat24.ua/send/h21hq)

## 🤝 Contributing

- Pull requests are welcome!
- Please read [CONTRIBUTING.md](CONTRIBUTING.md).
- All feedback, issues, and PRs appreciated.

---

## 🌍 Community

- [Discussions](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/discussions)
- [Report an Issue](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/issues)

---
