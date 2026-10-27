# Dashboard — SCADA Visualization

Live process visualization for the water tank system with built-in
attack simulation and ZTA toggle.

---

## Files

| File | Purpose |
|---|---|
| `scada_dashboard.html` | Main SCADA dashboard (HTML5/JavaScript/SVG) |
| `scada_bridge.py` | WebSocket bridge between PLC and browser |

---

## Features

- **Animated process view** — tanks fill visually, pipes animate, valves change color
- **Live readings** — main tank, 3 sub-tanks, 3 valves updated every 500ms
- **Pump control** — START/STOP pump from dashboard
- **Valve override** — manually set each valve to AUTO / OPEN / CLOSE
- **Attack buttons** — run all 5 attacks from the dashboard
- **ZT security toggle** — enable/disable Zero Trust with one click
- **System log** — all events logged in real time on the dashboard
- **ZT statistics** — blocked and allowed counters update live

---

## How to Run

### Step 1 — Start the bridge

```bash
python3 dashboard/scada_bridge.py
```

Wait for:
```
[BRIDGE] Connected to OpenPLC at localhost:502
[BRIDGE] Dashboard served at http://localhost:8888/scada_dashboard.html
```

### Step 2 — Open the dashboard

```
http://localhost:8888/scada_dashboard.html
```

If you see an old cached version press **Ctrl + Shift + R** in Firefox.

### Step 3 — Use the dashboard

1. Click **START PUMP** — tanks begin filling
2. Watch the animated SVG diagram update live
3. Turn ZT toggle **OFF** → click any attack button → see it succeed
4. Turn ZT toggle **ON** → click same attack → see it BLOCKED
5. Click **RESET ALL** to restore clean state between attacks

---

## Offline Mode

If `scada_bridge.py` is not running, the dashboard automatically switches
to **simulation mode** — the ZTA logic still works for demo purposes
but data is not coming from a real PLC.

The bridge connection status is shown in the bottom-right panel of the dashboard.
