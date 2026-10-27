from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient('localhost', port=502)
client.connect()

client.write_registers(address=1, values=[0, 0, 0])
client.write_register(address=10, value=400)
time.sleep(0.5)

print("Watching tank levels (Ctrl+C to stop)...\n")
print(f"{'Main':>8} {'Tank1':>8} {'Tank2':>8} {'Tank3':>8} {'V1':>5} {'V2':>5} {'V3':>5}")
print("-" * 55)

try:
    while True:
        regs  = client.read_holding_registers(address=1, count=3)
        main  = client.read_holding_registers(address=10, count=1)
        coils = client.read_coils(address=0, count=3)

        if not regs.isError() and not main.isError() and not coils.isError():
            t1, t2, t3 = regs.registers
            ml = main.registers[0]
            v1, v2, v3 = coils.bits[:3]
            print(f"{ml:>8} {t1:>8} {t2:>8} {t3:>8} {str(v1):>5} {str(v2):>5} {str(v3):>5}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nDone.")
    client.close()
