# 🛴 KuKirin G4 BLE Control — Read‑only Mode HUD

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![BLE](https://img.shields.io/badge/BLE-bleak-informational)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey)

Ultra‑low‑latency **read‑only** toolkit to monitor the **riding mode** of a *KuKirin G4* scooter over **Bluetooth Low Energy (BLE)**.  
No writes, no DFU, no OTA — **status stream only** (safe by design).

---

## 🔗 Quick Links
- ▶️ **Run**: `python3 ble_modes_live_ultra.py`
- 📦 **Install deps**: `pip install -r requirements.txt`
- 📄 **License**: MIT (see [LICENSE](LICENSE))

---

## 🧭 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [Install](#-install)
- [Usage](#-usage)
- [Output Sample](#-output-sample)
- [Protocol Notes](#-protocol-notes)
- [Performance Notes](#-performance-notes)
- [Repository Layout](#-repository-layout)
- [Troubleshooting](#-troubleshooting)
- [Disclaimer](#-disclaimer)
- [License](#-license)

---

## 📝 Overview
The main script **`ble_modes_live_ultra.py`** subscribes to the controller’s **FFF2** notifications and prints the **current mode** (ECO / SPORT / RACE) in real time with very small delay.  
It is **read‑only** and safe — the script never writes to the scooter.

> TL;DR: go to [Install](#-install), then [Usage](#-usage) and watch the mode change live.

---

## ✨ Features
- ✅ Scan for nearby BLE devices and **choose** your G4 from a list
- ✅ Live **MODE** readout on one terminal line (ANSI colors)
- ✅ **Read‑only** subscription to **FFF2** (safe)
- ✅ Noise filter using a **gate** byte
- 🧰 Clean code, easy to extend (CSV/JSON logging, UI later)

---

## 🛠 Install
```bash
git clone https://github.com/maksdoner/Kukirin-G4-Bluetooth-Control.git
cd Kukirin-G4-Bluetooth-Control
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```
> Needs **Python 3.10+** and Bluetooth enabled. Tested on **macOS**; Linux should work with correct BLE permissions.

---

## 🕹 Usage
1. Start the script:
   ```bash
   python3 ble_modes_live_ultra.py
   ```
2. Wait ~6 seconds for scan results, then **type the number** of your KuKirin G4.  
3. Watch the **MODE** update live. Press **Ctrl + C** to exit.

---

## 📟 Output Sample
```
[12:29:10] Scanning 6s…
#  NAME                      ADDRESS                               RSSI
-- ------------------------ ------------------------------------ -----
 1 KuKirin G4               XX:XX:XX:XX:XX:XX                      -53

[12:29:18] Connecting to XX:XX:… (KuKirin G4)…
[12:29:19] Connected. Subscribing to FFF2… (READ-ONLY)
MODE: ECO
MODE: SPORT
MODE: RACE
```

---

## 🧪 Protocol Notes
- **Characteristic**: subscribes to `FFF2` (`0000fff2-0000-1000-8000-00805f9b34fb`).
- **Gate filter**: a frame is accepted only if `frame[6] == 0x00`.
- **Mode byte**: `frame[5]` is the mode:
  - `0x01` → **ECO**
  - `0x02` → **SPORT**
  - `0x03` → **RACE**

The script prints **directly from the BLE callback** to reduce delay and updates the line **only when the mode changes**.

---

## ⚡ Performance Notes
- Optional speed‑up: **uvloop** on Unix (`pip install uvloop`).
- Minimal work inside the notification callback (fast).
- ANSI colors are used; please run in a terminal that supports colors.

---

## 🗂 Repository Layout
```
.
├─ ble_modes_live_ultra.py  # READ‑ONLY, ultra‑low‑latency mode HUD
├─ README.md
├─ LICENSE                  # MIT
├─ requirements.txt
└─ .gitignore
```

If you add another script (e.g., a logger), describe the difference here (HUD vs logging).

---

## 🧩 Troubleshooting
- **No devices found** → move closer, turn Bluetooth on, close other BT apps.
- **Permission error (Linux)** → check BLE permissions or try `sudo` (with care).
- **No colors** → your terminal may not support ANSI colors; it still works.
- **Connect fails** → re‑power Bluetooth, or reboot the scooter and try again.

---

## ⚠ Disclaimer
This project is for **research and educational purposes**. It is **read‑only**.  
Writing to the controller is out of scope and may cause unexpected behaviour. The author is not affiliated with KuKirin.

---

## 📄 License
MIT — see [LICENSE](LICENSE).
