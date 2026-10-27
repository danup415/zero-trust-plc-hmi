# Zero Trust Architecture for PLC–HMI Communication in Industrial Control Systems

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![OpenPLC](https://img.shields.io/badge/PLC-OpenPLC_v3-orange)
![Protocol](https://img.shields.io/badge/Protocol-Modbus_TCP-red)
![Security](https://img.shields.io/badge/Security-Zero_Trust_mTLS-green)
![Platform](https://img.shields.io/badge/Platform-Ubuntu_22.04-purple)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## What This Project Does

**Modbus TCP** — used in 90% of industrial control systems worldwide — has **zero built-in security**.
No authentication, no encryption, no access control.
Any device on the network can send commands to a PLC with no credentials.

This project implements a **Zero Trust Architecture (ZTA)** that sits between an HMI and a PLC,
enforcing:

- **Mutual TLS (mTLS)** — both the HMI and the proxy verify each other's identity via X.509 certificates
- **Function-code policy** — only read operations (FC01–FC04) are allowed; all writes are blocked
- **Full audit logging** — every command is logged with a cryptographic identity
- **Zero PLC changes** — the PLC firmware and configuration are never modified

Five attack types are demonstrated and blocked:
valve force, sensor spoofing, supply depletion, multi-vector chaos, and replay attacks.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Zero Trust Architecture                       │
│                                                                  │
│  ┌──────────┐   mTLS    ┌─────────────────┐  TCP  ┌─────────┐  │
│  │   HMI    │ ────────► │   ZT Proxy      │ ────► │   PLC   │  │
│  │ Node-RED │  Port 5020 │  (zt_proxy.py)  │ Port  │OpenPLC  │  │
│  └──────────┘           │  Policy Engine  │  502  └─────────┘  │
│                         │  Audit Logger   │                     │
│  ┌──────────┐           └─────────────────┘                     │
│  │ Attacker │ ──────► REJECTED (no cert / write blocked)        │
│  └──────────┘                                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
zero-trust-plc-hmi/
├── README.md                   ← You are here
├── LICENSE                     ← MIT License
├── .gitignore                  ← Ignores certs, logs, __pycache__
│
├── plc/                        ← PLC control program
│   ├── water_tank.st           ← IEC 61131-3 Structured Text program
│   └── README.md               ← How to upload to OpenPLC Runtime
│
├── proxy/                      ← Zero Trust security layer
│   ├── zt_proxy.py             ← Main proxy (mTLS + policy engine)
│   ├── zt_hmi_client.py        ← Trusted HMI client (with cert)
│   └── README.md               ← How to configure and run the proxy
│
├── attacks/                    ← Attack simulation scripts
│   ├── attack_valves.py        ← A1: Force valve open/close (FC05)
│   ├── attack_spoof.py         ← A2: Sensor register spoofing (FC10)
│   ├── attack_drain.py         ← A3: Main tank depletion DoS (FC06)
│   ├── attack_replay.py        ← A4: Raw packet replay attack
│   └── reset_system.py         ← Reset PLC to clean state
│
├── dashboard/                  ← SCADA visualization
│   ├── scada_dashboard.html    ← Live SCADA dashboard (HTML5)
│   └── scada_bridge.py         ← WebSocket bridge (PLC ↔ browser)
│
├── hmi/                        ← Node-RED HMI
│   ├── node_red_flow.json      ← Importable Node-RED flow
│   └── README.md               ← How to import and configure
│
├── certs/                      ← Certificate infrastructure
│   ├── generate_certs.sh       ← One-click PKI setup script
│   └── README.md               ← PKI explanation (no real certs committed)
│
├── monitoring/                 ← Network captures
│   ├── without_zta.pcapng      ← Wireshark capture without ZTA
│   ├── with_zta.pcapng         ← Wireshark capture with ZTA active
│   └── README.md               ← How to open and analyze captures
│
├── docs/                       ← Research documentation
│   ├── ZTA_ICS_IEEE.tex        ← IEEE LaTeX research paper
│   ├── architecture_diagram.png← System architecture diagram
│   └── demo_guide.md           ← Step-by-step demo guide
│
└── scripts/                    ← Startup and utility scripts
    ├── start_plc.sh            ← Start OpenPLC with correct permissions
    ├── watch_tanks.py          ← Live terminal monitoring
    └── setup.sh                ← Install all dependencies
```

---

## Prerequisites

- **OS:** Ubuntu 22.04 LTS (native or VirtualBox VM — recommended 4GB RAM, 2 CPU cores)
- **Python:** 3.10 or higher
- **Node.js:** v18 or higher
- **OpenSSL:** 3.x (pre-installed on Ubuntu 22.04)

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/zero-trust-plc-hmi.git
cd zero-trust-plc-hmi
```

### Step 2 — Run the setup script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This installs:
- OpenPLC Runtime v3
- Python packages: `pymodbus==3.6.9`, `websockets`, `scapy`
- Node-RED + Modbus and Dashboard palettes
- Wireshark

### Step 3 — Generate certificates

```bash
chmod +x certs/generate_certs.sh
./certs/generate_certs.sh
```

This creates the Certificate Authority, PLC server certificate,
and HMI client certificate in the `certs/` folder.

---

## Running the Project

Open **5 terminals** and run each command in order.

### Terminal 1 — Start OpenPLC Runtime

```bash
chmod +x scripts/start_plc.sh
./scripts/start_plc.sh
```

Wait until you see:
```
Server: Listening on port 502
```

Then open `http://localhost:8080` in your browser.
- Login: `openplc / openplc`
- Go to **Programs** → click `water_tank` → **Launch Program** → **Start PLC**

### Terminal 2 — Start Node-RED HMI

```bash
node-red &
```

Open `http://localhost:1880` → click **Deploy**.
Dashboard available at `http://localhost:1880/ui`.

### Terminal 3 — Start Zero Trust Proxy

```bash
python3 proxy/zt_proxy.py
```

Wait until you see:
```
Zero Trust Modbus Proxy
Listening on port 5020 (mTLS)
Forwarding to PLC at 127.0.0.1:502
```

### Terminal 4 — Start SCADA Bridge

```bash
python3 dashboard/scada_bridge.py
```

Wait until you see:
```
[BRIDGE] Connected to OpenPLC at localhost:502
[BRIDGE] Dashboard served at http://localhost:8888/scada_dashboard.html
```

### Terminal 5 — Live Tank Monitor

```bash
python3 scripts/watch_tanks.py
```

This initializes the main tank to 400 and shows live readings:
```
    Main    Tank1    Tank2    Tank3    V1    V2    V3
-------------------------------------------------------
     397        1        1        1  True  True  True
     394        2        2        2  True  True  True
```

### Open the SCADA Dashboard

```bash
firefox http://localhost:8888/scada_dashboard.html
```

Press **Ctrl + Shift + R** to hard refresh if you see a cached version.

---

## Attack Demonstrations

### Without Zero Trust (ZT toggle OFF)

Run each attack with the SCADA dashboard open to see the effect live.

```bash
# Reset system to clean state first — always do this before each attack
python3 attacks/reset_system.py

# Attack 1: Force valves open/closed (FC05)
python3 attacks/attack_valves.py

# Reset, then Attack 2: Sensor spoofing (FC10)
python3 attacks/reset_system.py
python3 attacks/attack_spoof.py

# Reset, then Attack 3: Main tank drain DoS (FC06)
python3 attacks/reset_system.py
python3 attacks/attack_drain.py

# Reset, then Attack 4: Replay attack (raw socket)
python3 attacks/reset_system.py
python3 attacks/attack_replay.py
```

### With Zero Trust Active (ZT toggle ON)

Enable the ZT toggle on the SCADA dashboard, then re-run the same attacks.
All are blocked. Check Terminal 3 to see the proxy log.

---

## Results Summary

| Attack | Without ZTA | With ZTA | Block Mechanism |
|---|---|---|---|
| A1: Valve Force | ✅ Succeeds | ❌ Blocked | FC05 policy deny |
| A2: Sensor Spoof | ✅ Succeeds | ❌ Blocked | FC10 policy deny |
| A3: Tank Drain DoS | ✅ Succeeds | ❌ Blocked | FC06 policy deny |
| A4: Multi-Vector | ✅ Succeeds | ❌ Blocked | All FC policy deny |
| A5: Replay | ✅ Succeeds | ❌ Blocked | TLS session keys |

**100% attack mitigation rate | 2.3ms mean latency overhead | 98.6% availability**

---

## Technology Stack

| Component | Technology | Version |
|---|---|---|
| PLC Runtime | OpenPLC Runtime | v3.0 |
| PLC Language | IEC 61131-3 Structured Text | — |
| Communication Protocol | Modbus TCP | Port 502 |
| ZT Proxy | Python ssl + socket | 3.12 |
| Certificate Authority | OpenSSL | 3.0.2 |
| HMI | Node-RED | 4.1.7 |
| SCADA Dashboard | HTML5 + WebSocket | Custom |
| Attack Tools | pymodbus + Scapy | 3.6.9 |
| Network Analysis | Wireshark | 4.2.5 |
| OS | Ubuntu 22.04 LTS | Kernel 6.5 |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Permission denied` on port 502 | Run `./scripts/start_plc.sh` (applies setcap automatically) |
| Port 8080 already in use | `sudo fuser -k 8080/tcp && ./scripts/start_plc.sh` |
| Port 5020 already in use | `sudo fuser -k 5020/tcp` |
| Port 8888 already in use | `sudo fuser -k 8888/tcp` |
| Dashboard shows old version | Press `Ctrl + Shift + R` in Firefox |
| All tank values showing 0 | Run `python3 scripts/watch_tanks.py` to reinitialize |
| ZT proxy SSL error | Run `./certs/generate_certs.sh` to regenerate certs |

---

## Research Paper

An IEEE-format research paper is available in `docs/ZTA_ICS_IEEE.tex`.

**Title:** Zero Trust Architecture for Securing PLC–HMI Communication
in Industrial Control Systems: mTLS-Based Proxy Design, Policy Enforcement,
and Empirical Attack Validation

Compile with:
```bash
sudo apt install texlive-full -y
cd docs
pdflatex ZTA_ICS_IEEE.tex
bibtex ZTA_ICS_IEEE
pdflatex ZTA_ICS_IEEE.tex
pdflatex ZTA_ICS_IEEE.tex
```

---

## License

MIT License — free to use, modify, and distribute with attribution.
See [LICENSE](LICENSE) for full terms.

---

## Author

**Anup S.**
B.Tech Instrumentation and Control Engineering
Vishwakarma Institute of Technology (VIT), Pune
