# dbus-huaweisun2000-pvinverter

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/taras-kolodchyn/dbus-huaweisun2000-pvinverter)](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/releases)
![Platform](https://img.shields.io/badge/platform-Venus%20OS%20(Cerbo%20GX)-informational)
[![Python Version](https://img.shields.io/badge/python-3.12.9-blue.svg)](https://www.python.org/downloads/release/python-3129/)
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

- **Victron Cerbo GX** or compatible device with Venus OS (**v3.60 – v3.65** verified)
- **Huawei SUN2000 inverter** (any recent model)
- **Inverter WiFi or LAN access** (Modbus TCP port 502 open)
- **Python 3.x** (pre-installed on Venus OS)

> ⚠️ **Venus OS firmware below v3.60 is not supported!**

---

## 🧪 Tested Devices & Compatibility

| Device           | Version                       | Status         |
|------------------|-------------------------------|----------------|
| Cerbo GX         | Venus OS v3.60 – v3.65        | Supported      |
| SUN2000-30KTL-M3 | Latest firmware               | Supported      |

- Venus OS versions 3.60–3.65 have been verified as working.
- Other recent Huawei SUN2000 inverters should work if they support Modbus TCP.
- See [Issues](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/issues) for compatibility reports.

---

## 📥 Installation

### 1. Download and deploy

**From GitHub Releases (recommended for stable):**

```bash
cd /data
wget https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/releases/download/v1.0.0/dbus-huaweisun2000-pvinverter-v1.0.0.zip
unzip dbus-huaweisun2000-pvinverter-v1.0.0.zip
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
unzip main.zip
mv dbus-huaweisun2000-pvinverter-main dbus-huaweisun2000-pvinverter
chmod +x dbus-huaweisun2000-pvinverter/install.sh
sh dbus-huaweisun2000-pvinverter/install.sh
```

---

## ▶️ Usage

- Service autostarts after installation.
- **Check status:** `svstat /service/dbus-huaweisun2000-pvinverter`
- **Manual debug:**  
  `python /data/dbus-huaweisun2000-pvinverter/dbus-huaweisun2000-pvinverter.py`
- **Logs:**  
  `tail -f /var/log/dbus-huaweisun2000/current | tai64nlocal`

## ⚠️ New UI Settings Notice

As of Venus OS v3.60–v3.65, the **New UI (GUI‑v2)** does not display the full settings menu for third‑party PV inverter drivers.  
If you need to change the inverter’s Modbus host, port, unit, or position:

- **Use the Classic UI**:  
  Go to *Menu → Settings → PV Inverters → Huawei SUN2000*

- **Or change values directly via D‑Bus** (Remote Console → `dbus-spy`):  
  1. Open `com.victronenergy.pvinverter.sun2000`  
  2. Edit `/Position` (0 = AC Input, 1 = AC‑Out 1, 2 = AC‑Out 2)  
  3. Update Modbus settings under `com.victronenergy.settings`

Once Victron adds support for custom settings pages in the New UI, these options will appear directly there.

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

### Classic UI

![Classic UI Main Screen](img/classic-ui/classic-ui-1.png)  
![Classic UI Details](img/classic-ui/classic-ui-2.png)  

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
- Please read [CONTRIBUTING.md](CONTRIBUTING.md) (to be added).
- All feedback, issues, and PRs appreciated.

---

## 🌍 Community

- [Discussions](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/discussions)
- [Report an Issue](https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/issues)

---