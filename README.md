# dbus-huaweisun2000-pvinverter

A D-Bus driver for integrating Huawei SUN2000 inverters into Victron Cerbo GX / Venus OS.

# Overview

This project provides seamless integration of Huawei SUN2000 PV inverters with Victron Venus OS and the VRM Portal.  
It allows Venus OS to monitor key inverter parameters over Modbus TCP using the built-in WiFi of the inverter, without requiring additional hardware.

# Table of Contents

- [Features](#features)  
- [Requirements](#requirements)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Updating](#updating)  
- [Uninstall](#uninstall)  
- [Screenshots](#screenshots)  
- [Troubleshooting](#troubleshooting)  
- [License](#license)  

# Features

- Reads live data from Huawei SUN2000 inverters 
- Supports Venus OS devices (e.g., Cerbo GX)  
- Full VRM Portal integration  
- Clean D-Bus interface for easy access by other Venus OS apps  
- Simple installation and update scripts  
- Automatic reconnection and error handling  
- Open source, easily extendable  


# Requirements

- Venus OS device (e.g., Cerbo GX, Raspberry Pi with Venus OS)  
- Huawei SUN2000 inverter (any recent model)  
- Access to the inverter’s WiFi or LAN  
- Python 3.x (standard on Venus OS)  
- TCP port 502 must be open and accessible between Venus OS and the inverter for Modbus TCP communication  

## Compatibility & Tested Devices

> **Note:**  
> Venus OS firmware versions **below v3.60 are not supported** and have not been tested.  
> Please ensure your device is running Venus OS v3.60 or higher for proper operation.

This integration was tested on the following hardware and firmware versions:

- **Victron Cerbo GX**
  - *Venus OS firmware:* **v3.60**
- **Huawei Inverter:**
  - *Model:* **SUN2000-30KTL-M3**

Other recent Huawei SUN2000 inverters should also be compatible if they support Modbus TCP.
If you successfully use this integration with other hardware versions or firmware, feel free to open an issue or a pull request to update the list!

## Version Compatibility

This project provides separate service releases for different Venus OS firmware versions.

| Service Release | Supported Venus OS Firmware| Status                |
|-----------------|----------------------------|-----------------------|
| **v1.0.0+**     | v3.60 and above            | Recommended/Supported |


> **Note:**  
> Firmware versions below **v3.60** are *not* supported in the main branch.  
> If you are running an older Venus OS version, please use the appropriate legacy service release.

If you are unsure which version to use, check your Cerbo GX firmware version (`Settings → Device → Firmware`).  
If you successfully use this integration with older firmware, please report your findings via an issue or pull request!

# Installation

Copy or clone the repository to your Venus OS device:  

```bash
scp -r dbus-huaweisun2000-pvinverter root@venus:/data/
```

Replace `venus` with your Venus OS device's IP address or hostname.  

Or download directly on the device:  

```bash
cd /data
wget https://github.com/taras-kolodchyn/dbus-huaweisun2000-pvinverter/archive/refs/heads/main.zip
unzip main.zip
mv dbus-huaweisun2000-pvinverter-main dbus-huaweisun2000-pvinverter
chmod +x dbus-huaweisun2000-pvinverter/install.sh
sh dbus-huaweisun2000-pvinverter/install.sh
rm main.zip
```

# Usage

- Service will auto-start after installation.  
- To check status: `svstat /service/dbus-huaweisun2000-pvinverter`  
- For debugging, run the main script manually:  
  `python /data/dbus-huaweisun2000-pvinverter/dbus-huaweisun2000-pvinverter.py`  
- Service logs can be viewed for troubleshooting and monitoring (see Troubleshooting section for details).  
- Service management commands (start, stop, restart) can be used to control the driver as needed.  

# Updating

After updating files or pulling new changes:  

```bash
sh /data/dbus-huaweisun2000-pvinverter/restart.sh
```

# Uninstall

```bash
sh /data/dbus-huaweisun2000-pvinverter/uninstall.sh
rm -r /data/dbus-huaweisun2000-pvinverter/
```

# Screenshots

## New UI

_Main page: Live inverter status and summary_  
- ![New UI Main Overview](img/new-ui/main-ui-1.png "New UI Main Overview")

_Phase details and energy history_  
- ![New UI Details](img/new-ui/main-ui-2.png "New UI Phase Details and Energy History")

_Device details_  
- ![New UI Settings](img/new-ui/main-ui-3.png "New UI Device Settings")  

*See all screenshots in the [img/new-ui](img/new-ui/) folder.*

## VRM Portal

_Main PV inverter page in VRM portal_  
- ![VRM Portal Main Page](img/vrm/vrm-01.png "VRM Portal Main PV Inverter Page")

_Devices page in VRM portal_  
- ![VRM Portal Devices Page](img/vrm/vrm-02.png "VRM Portal Devices Page")

*See all screenshots in the [img/vrm](img/vrm/) folder.*

## Classic UI

_Classic UI: Main screen_  
- ![Classic UI Main Screen](img/classic-ui/classic-ui-1.png "Classic UI Main Screen")  

_Classic UI: Inverter details_  
- ![Classic UI Details](img/classic-ui/classic-ui-2.png "Classic UI Inverter Details")  

*See all screenshots in the [img/classic-ui](img/classic-ui/) folder.*

# Troubleshooting

- Check logs by running:  
  ```bash
  tail -f /var/log/dbus-huaweisun2000/current | tai64nlocal
  ```  
  This will show real-time service logs with human-readable timestamps.  
- If the service keeps restarting, try running the main script manually to see error messages directly.  
- No data appearing in VRM Portal? Verify the Modbus settings including inverter IP address, TCP port (default 502), and Modbus unit ID are correctly configured.  
- Ensure network connectivity between Venus OS and the inverter is stable and that TCP port 502 is not blocked by firewalls.  

# License

This project is licensed under the [MIT License](LICENSE).
