from pymodbus.client import ModbusTcpClient
import ssl
import socket
import struct
import time

CERT_DIR = "/home/anup/zt_certs"

class ZTModbusClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.transaction_id = 0

    def connect(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_cert_chain(
            certfile=f"{CERT_DIR}/hmi.crt",
            keyfile=f"{CERT_DIR}/hmi.key"
        )
        context.load_verify_locations(cafile=f"{CERT_DIR}/ca.crt")
        context.check_hostname = False

        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = context.wrap_socket(raw_sock)
        self.sock.connect((self.host, self.port))
        print(f"[HMI] Connected to ZT proxy with valid certificate")
        return True

    def read_holding_registers(self, address, count):
        self.transaction_id += 1
        request = struct.pack('>HHHBBHH',
            self.transaction_id, 0, 6, 1, 0x03, address, count)
        self.sock.send(request)
        response = self.sock.recv(1024)
        if len(response) > 9:
            values = struct.unpack(f'>{count}H', response[9:9+count*2])
            return list(values)
        return []

    def read_coils(self, address, count):
        self.transaction_id += 1
        request = struct.pack('>HHHBBHH',
            self.transaction_id, 0, 6, 1, 0x01, address, count)
        self.sock.send(request)
        response = self.sock.recv(1024)
        if len(response) > 9:
            byte_val = response[9]
            return [bool(byte_val & (1 << i)) for i in range(count)]
        return []

    def close(self):
        if self.sock:
            self.sock.close()

client = ZTModbusClient('127.0.0.1', 5020)
client.connect()

print("\nReading tank levels via Zero Trust proxy...\n")
print(f"{'Main':>8} {'Tank1':>8} {'Tank2':>8} {'Tank3':>8} {'V1':>5} {'V2':>5} {'V3':>5}")
print("-" * 55)

try:
    while True:
        tanks  = client.read_holding_registers(address=1, count=3)
        main   = client.read_holding_registers(address=10, count=1)
        valves = client.read_coils(address=0, count=3)

        if tanks and main and valves:
            t1, t2, t3 = tanks
            ml = main[0]
            v1, v2, v3 = valves
            print(f"{ml:>8} {t1:>8} {t2:>8} {t3:>8} {str(v1):>5} {str(v2):>5} {str(v3):>5}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nDone.")
    client.close()
