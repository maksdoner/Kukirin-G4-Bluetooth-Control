#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maksdoner
#
# KuKirin G4 — BLE Mode HUD (READ-ONLY)
# -------------------------------------
# Simple English (A2).
#
# What this script does:
# 1) Scan BLE devices for 6 seconds.
# 2) You choose your KuKirin G4 by number.
# 3) It connects and LISTENS (read-only) to FFF2 notifications.
# 4) It prints the current MODE (ECO / SPORT / RACE) with colors.
#
# Important:
# - This script DOES NOT write anything to the scooter.
# - No OTA / DFU / write. It is safe (read-only).
#
# Requirements:
# - Python 3.10+
# - bleak (pip install bleak)
# - (optional) uvloop on macOS/Linux (pip install uvloop)
#
# Run:
#   python3 ble_modes_live_ultra.py
#
# Exit:
#   Press Ctrl + C
#
# Protocol (from logs and tests):
# - We use notifications from characteristic FFF2 (UUID below).
# - We read the bytes in the frame:
#     * frame[6] == 0x00  -> this is a "gate" check (filter noise)
#     * frame[5] is MODE:
#         0x01 = ECO
#         0x02 = SPORT
#         0x03 = RACE

import sys
import asyncio
from datetime import datetime, timezone

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

# (optional) faster event loop on Unix
try:
    import uvloop  # type: ignore
    uvloop.install()
except Exception:
    pass

# ====== CONSTANTS (Protocol) ==================================================
FFF2_UUID    = "0000fff2-0000-1000-8000-00805f9b34fb"
GATE_OFFSET  = 6
GATE_VALUE   = 0x00
MODE_OFFSET  = 5
MODE_MAP     = {0x01: "ECO", 0x02: "SPORT", 0x03: "RACE"}

# ====== SETTINGS ==============================================================
SCAN_SECONDS     = 6     # how long to scan
CONNECT_TIMEOUT  = 10    # seconds

# ====== Small helpers (colors and time) ======================================
def color(txt: str, code: str) -> str:
    return f"\033[{code}m{txt}\033[0m"

GREEN = "32"
BLUE  = "34"
RED   = "31"
GREY  = "90"
BOLD  = "1"

def ceco()   -> str: return f"\033[{BOLD};{GREEN}mECO\033[0m"
def csport() -> str: return f"\033[{BOLD};{BLUE}mSPORT\033[0m"
def crace()  -> str: return f"\033[{BOLD};{RED}mRACE\033[0m"

def dim(s: str) -> str:
    return f"\033[{GREY}m{s}\033[0m"

def now_local_str() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")

# ====== Scan for BLE devices ==================================================
async def scan_devices(timeout: int = SCAN_SECONDS) -> list[BLEDevice]:
    print(dim(f"\n[{now_local_str()}] Scanning for {timeout}s… (close other BT apps)"))

    found: dict[str, BLEDevice] = {}

    def on_detect(d: BLEDevice, adv) -> None:
        # Save by address (unique)
        found[d.address] = d

    scanner = BleakScanner(detection_callback=on_detect)
    await scanner.start()
    await asyncio.sleep(timeout)
    await scanner.stop()

    devices = list(found.values())
    if not devices:
        print("No BLE devices found.")
        return []

    # Sort by RSSI (best signal first)
    def rssi_of(dev: BLEDevice) -> int:
        val = getattr(dev, "rssi", None)
        return val if isinstance(val, int) else -999

    devices.sort(key=rssi_of, reverse=True)

    # Show a simple table
    print("\n#  NAME                      ADDRESS                               RSSI")
    print("-- ------------------------ ------------------------------------ -----")
    for i, d in enumerate(devices, 1):
        name = (d.name or "(no name)")[:24]
        rssi = getattr(d, "rssi", "")
        print(f"{i:>2} {name:<24} {d.address:<36} {str(rssi):>5}")
    print()

    return devices

# ====== Live HUD (print from callback with very low delay) ====================
async def live_hud(client: BleakClient) -> None:
    last_mode: dict[str, str | None] = {"val": None}  # mutable holder

    # Pre-build lines for fast printing (no string build in callback)
    PREFIX = "MODE: "
    ECO_LINE   = "\r" + PREFIX + ceco()   + " " * 12
    SPORT_LINE = "\r" + PREFIX + csport() + " " * 12
    RACE_LINE  = "\r" + PREFIX + crace()  + " " * 12

    def on_notify(_handle: int, data: bytearray) -> None:
        # Very light parser
        if not data:
            return
        if len(data) <= max(GATE_OFFSET, MODE_OFFSET):
            return
        if data[GATE_OFFSET] != GATE_VALUE:
            return

        b = data[MODE_OFFSET]
        if b == 0x01:
            if last_mode["val"] != "ECO":
                sys.stdout.write(ECO_LINE)
                sys.stdout.flush()
                last_mode["val"] = "ECO"
        elif b == 0x02:
            if last_mode["val"] != "SPORT":
                sys.stdout.write(SPORT_LINE)
                sys.stdout.flush()
                last_mode["val"] = "SPORT"
        elif b == 0x03:
            if last_mode["val"] != "RACE":
                sys.stdout.write(RACE_LINE)
                sys.stdout.flush()
                last_mode["val"] = "RACE"
        # other bytes are ignored

    await client.start_notify(FFF2_UUID, on_notify)
    try:
        # Keep the program alive (until Ctrl+C)
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            await client.stop_notify(FFF2_UUID)
        except Exception:
            pass
        sys.stdout.write("\n")  # nice newline

# ====== Connect and run =======================================================
async def connect_and_run(device: BLEDevice) -> None:
    print(dim(f"[{now_local_str()}] Connecting to {device.address} ({device.name})…"))
    async with BleakClient(device, timeout=CONNECT_TIMEOUT) as client:
        # Check connection (different backends may behave differently)
        try:
            ic = getattr(client, "is_connected")
            ok = ic if isinstance(ic, bool) else bool(await ic)
        except Exception:
            ok = bool(getattr(client, "is_connected", False))
        if not ok:
            print("Could not connect.")
            return

        print(dim(f"[{now_local_str()}] Connected. Subscribing to FFF2 (READ-ONLY)…"))
        await live_hud(client)

# ====== Main loop =============================================================
async def main() -> None:
    while True:
        devices = await scan_devices()
        if not devices:
            return

        s = input(f"Choose number 1..{len(devices)} (r = rescan, q = quit): ").strip().lower()
        if s == "q":
            return
        if s == "r":
            continue
        if not s.isdigit():
            print("Wrong input.")
            continue

        i = int(s) - 1
        if not (0 <= i < len(devices)):
            print("Out of range.")
            continue

        try:
            await connect_and_run(devices[i])
        except Exception as e:
            print("Session error:", e)
        print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
