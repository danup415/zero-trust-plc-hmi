import socket
import ssl
import threading
import struct
import logging
import datetime

logging.basicConfig(
    filename='/home/anup/zt_proxy.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ─── Policy: allowed Modbus function codes ───────────────────────────────────
ALLOWED_FUNCTION_CODES = {
    0x01: "Read Coils",
    0x02: "Read Discrete Inputs",
    0x03: "Read Holding Registers",
    0x04: "Read Input Registers",
}

BLOCKED_FUNCTION_CODES = {
    0x05: "Write Single Coil",
    0x06: "Write Single Register",
    0x0F: "Write Multiple Coils",
    0x10: "Write Multiple Registers",
}

CERT_DIR = "/home/anup/zt_certs"
LISTEN_PORT = 5020
PLC_HOST = "127.0.0.1"
PLC_PORT = 502

def parse_modbus_function(data):
    if len(data) >= 8:
        func_code = data[7]
        return func_code
    return None

def handle_client(conn, addr, context):
    try:
        tls_conn = context.wrap_socket(conn, server_side=True)
        cert = tls_conn.getpeercert()
        client_cn = dict(x[0] for x in cert['subject']).get('commonName', 'Unknown')

        logging.info(f"[CONNECTED] {addr[0]}:{addr[1]} | Identity: {client_cn}")
        print(f"[ZT] Connected: {client_cn} from {addr[0]}:{addr[1]}")

        # Connect to real PLC
        plc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        plc_sock.connect((PLC_HOST, PLC_PORT))

        while True:
            data = tls_conn.recv(1024)
            if not data:
                break

            func_code = parse_modbus_function(data)

            if func_code in BLOCKED_FUNCTION_CODES:
                action = BLOCKED_FUNCTION_CODES[func_code]
                logging.warning(f"[BLOCKED] {client_cn} attempted {action} (FC {func_code:#04x})")
                print(f"[ZT BLOCKED] {client_cn} tried: {action}")

                # Send Modbus exception response (illegal function)
                error_response = bytearray(data[:6])
                error_response.append(data[7] | 0x80)
                error_response.append(0x01)
                tls_conn.send(bytes(error_response))
                continue

            elif func_code in ALLOWED_FUNCTION_CODES:
                action = ALLOWED_FUNCTION_CODES[func_code]
                logging.info(f"[ALLOWED] {client_cn} | {action} (FC {func_code:#04x})")
                print(f"[ZT ALLOWED] {client_cn}: {action}")

                plc_sock.send(data)
                response = plc_sock.recv(1024)
                tls_conn.send(response)

            else:
                logging.warning(f"[UNKNOWN] FC {func_code:#04x} from {client_cn} - blocked")
                print(f"[ZT UNKNOWN] FC {func_code:#04x} blocked")

    except ssl.SSLError as e:
        logging.error(f"[REJECTED] {addr[0]}:{addr[1]} - SSL Error: {e}")
        print(f"[ZT REJECTED] {addr[0]}:{addr[1]} - No valid certificate!")
    except Exception as e:
        logging.error(f"[ERROR] {addr[0]}:{addr[1]} - {e}")
    finally:
        try:
            tls_conn.close()
            plc_sock.close()
        except:
            pass
        logging.info(f"[DISCONNECTED] {addr[0]}:{addr[1]}")

def start_proxy():
    # TLS context for the proxy server
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=f"{CERT_DIR}/plc.crt",
        keyfile=f"{CERT_DIR}/plc.key"
    )
    context.load_verify_locations(cafile=f"{CERT_DIR}/ca.crt")
    context.verify_mode = ssl.CERT_REQUIRED  # enforce mTLS

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', LISTEN_PORT))
    server.listen(5)

    print(f"")
    print(f"  Zero Trust Modbus Proxy")
    print(f"  Listening on port {LISTEN_PORT} (mTLS)")
    print(f"  Forwarding to PLC at {PLC_HOST}:{PLC_PORT}")
    print(f"  Allowed FCs: READ only")
    print(f"  Blocked FCs: ALL WRITES")
    print(f"  Log: /home/anup/zt_proxy.log")
    print(f"")

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr, context))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    start_proxy()
