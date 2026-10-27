# Attacks — Simulation Scripts

Five attack scripts demonstrate the vulnerabilities of unprotected Modbus TCP
and validate that the ZTA proxy blocks all of them.

---

## Attack Overview

| Script | Attack Type | Modbus FC | Effect |
|---|---|---|---|
| `attack_valves.py` | Unauthorized valve control | FC05 | Forces valves open/closed |
| `attack_spoof.py` | Sensor data spoofing | FC06/FC10 | Writes fake tank levels |
| `attack_drain.py` | Main tank depletion DoS | FC06 | Sets main tank to 0, halts system |
| `attack_replay.py` | Session replay | Raw socket | Replays captured packet 4 times |
| `reset_system.py` | System reset | FC06/FC10 | Restores clean state before each attack |

---

## How to Run

### Always reset before each attack

```bash
python3 attacks/reset_system.py
```

This sets: main tank = 400, sub-tanks = 0, valves = closed.

### Run attacks WITHOUT ZTA (ZT toggle OFF on dashboard)

```bash
# Attack 1 — Valve force
python3 attacks/reset_system.py
python3 attacks/attack_valves.py

# Attack 2 — Sensor spoof
python3 attacks/reset_system.py
python3 attacks/attack_spoof.py

# Attack 3 — Tank drain
python3 attacks/reset_system.py
python3 attacks/attack_drain.py

# Attack 4 — Replay
python3 attacks/reset_system.py
python3 attacks/attack_replay.py
```

### Re-run WITH ZTA active (ZT toggle ON on dashboard)

Same commands — but now all attacks are blocked.
Check the ZT proxy terminal to see BLOCKED log entries.

---

## What to Watch While Attacks Run

Keep `python3 scripts/watch_tanks.py` running in a separate terminal.
Each attack produces a distinct visible change:

| Attack | What changes in watch_tanks.py |
|---|---|
| Valve force | V1/V2/V3 flip False → True or True → False |
| Sensor spoof | Tank levels jump to 0, then 99, then mixed |
| Tank drain | Main tank drops to 0, all valves go False |
| Replay | Only V1 closes 4 times while V2/V3 stay open |

---

## Requirements

- OpenPLC must be running on port 502
- ZT proxy must be OFF (port 5020) to run attacks on port 502 directly
- Python pymodbus 3.6.9 installed
