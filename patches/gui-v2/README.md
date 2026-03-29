# GUI-v2 Browser Patch

This directory contains upstream patches for [`victronenergy/gui-v2`](https://github.com/victronenergy/gui-v2).

## Why this exists

The `gui-v2/` overlay shipped in this repository affects the native GX display only.  
Browser Remote Console uses the compiled `venus-gui-v2.wasm`, so browser-specific UI fixes must be applied to upstream `gui-v2`, rebuilt, and deployed to the GX web root.

## Included patch

- `0001-huawei-pvinverter-ac-summary-fallback.patch`

This patch makes multi-phase PV inverters use `/Ac/Voltage` and `/Ac/Current` as summary fallbacks when they are available. That fixes Huawei SUN2000 voltage/current display in browser gui-v2 while keeping the existing `NaN` behavior for PV inverter services that do not expose those summary paths.

It also adds a `solarinputmodel` test case for a Huawei-like service shape.

## How to use it

1. Clone upstream `gui-v2`:
   ```bash
   git clone https://github.com/victronenergy/gui-v2
   cd gui-v2
   ```
2. Apply the patch:
   ```bash
   git apply /data/dbus-huaweisun2000-pvinverter/patches/gui-v2/0001-huawei-pvinverter-ac-summary-fallback.patch
   ```
3. Build the browser bundle by following upstream gui-v2 build instructions.
4. Deploy the generated browser assets, including `venus-gui-v2.wasm`, to `/var/www/venus/gui-v2/` on the GX device.

## Reference baseline

The patch was prepared against upstream `victronenergy/gui-v2` main at commit `526045d`.
