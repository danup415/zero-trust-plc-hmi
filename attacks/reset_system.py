from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient('localhost', port=502)
client.connect()

client.write_register(address=10, value=400)
client.write_registers(address=1, values=[0, 0, 0])
client.write_coil(address=0, value=False)
client.write_coil(address=1, value=False)
client.write_coil(address=2, value=False)
time.sleep(0.5)

main  = client.read_holding_registers(address=10, count=1)
tanks = client.read_holding_registers(address=1, count=3)
coils = client.read_coils(address=0, count=3)

print("System RESET complete:")
print(f"  Main tank : {main.registers[0]} / 400")
print(f"  Tanks     : {tanks.registers}")
print(f"  Valves    : {coils.bits[:3]}")
client.close()
