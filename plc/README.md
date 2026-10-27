# PLC — Water Tank Control Program

This folder contains the IEC 61131-3 Structured Text program that runs on
OpenPLC Runtime to control the water distribution system.

---

## What the Program Does

- **Main tank** holds 400 units of water
- **3 sub-tanks** each hold up to 100 units
- Each sub-tank has a valve that opens automatically when the tank is below 80%
- All three valves fill simultaneously
- When a tank reaches 80%, its valve closes

## Control Logic (simplified)

```
For each sub-tank (1, 2, 3):
  IF tank_level < 80% AND main_tank > 0 THEN
    Open valve
  ELSE
    Close valve
```

## Variable to Modbus Address Mapping

| Variable | Address | Modbus Register |
|---|---|---|
| Main tank level | QW10 | Holding Register 10 |
| Sub-tank 1 level | QW1 | Holding Register 1 |
| Sub-tank 2 level | QW2 | Holding Register 2 |
| Sub-tank 3 level | QW3 | Holding Register 3 |
| Valve 1 | QX0.0 | Coil 0 |
| Valve 2 | QX0.1 | Coil 1 |
| Valve 3 | QX0.2 | Coil 2 |

---

## How to Upload to OpenPLC Runtime

### Step 1 — Make sure OpenPLC is running

```bash
./scripts/start_plc.sh
```

Wait for: `Server: Listening on port 502`

### Step 2 — Open the web interface

```
http://localhost:8080
```

Login: `openplc / openplc`

### Step 3 — Upload the program

1. Click **Programs** in the left menu
2. Click **Browse** → select `plc/water_tank.st`
3. Click **Upload Program**
4. Click on the uploaded program → **Launch Program**
5. Click **Start PLC** (green button)

Status should change to **Running: water_tank**

### Step 4 — Verify in Monitoring

Click **Monitoring** in the left menu.
You should see all 7 variables listed with their locations (QW1, QW2, QW3, QW10, QX0.0, etc.)

---

## Scan Cycle

The program runs every **500ms** (configured in the CONFIGURATION block at
the bottom of `water_tank.st`).
