# Proxy — Zero Trust Security Layer

This folder contains the core Zero Trust Architecture implementation.

---

## Files

| File | Purpose |
|---|---|
| `zt_proxy.py` | Main ZT proxy — mTLS + policy engine + audit log |
| `zt_hmi_client.py` | Trusted HMI client that connects using its certificate |

---

## How the Proxy Works

```
HMI (with certificate)
        │
        ▼ TLS handshake (port 5020)
  [ZT Proxy]
        │ Certificate check → identity extracted
        │ Function code check → policy enforced
        │ Audit log entry written
        ▼ Raw TCP (port 502)
  [OpenPLC PLC]
```

1. **mTLS handshake** — Both sides verify each other's certificate
2. **Identity extraction** — Certificate CN is logged (e.g. "HMI-Client")
3. **Policy check** — FC01/02/03/04 (reads) → ALLOWED; FC05/06/0F/10 (writes) → BLOCKED
4. **Audit log** — Every connection and command written to `zt_proxy.log`

---

## Prerequisites

Certificates must exist before running the proxy:

```bash
./certs/generate_certs.sh
```

---

## How to Run

### Start the ZT Proxy

```bash
python3 proxy/zt_proxy.py
```

Expected output:
```
  Zero Trust Modbus Proxy
  Listening on port 5020 (mTLS)
  Forwarding to PLC at 127.0.0.1:502
  Allowed FCs: READ only (FC01, FC02, FC03, FC04)
  Blocked FCs: ALL WRITES (FC05, FC06, FC0F, FC10)
  Log: /home/USER/zt_proxy.log
```

### Test with the Trusted HMI Client

In a second terminal:

```bash
python3 proxy/zt_hmi_client.py
```

You should see live tank readings flowing through the ZT proxy.

### Watch the Audit Log

```bash
tail -f ~/zt_proxy.log
```

---

## What Gets Blocked

| Attacker Type | What Happens |
|---|---|
| No certificate | TLS handshake fails — connection rejected before any data |
| Self-signed cert (not from CA) | Certificate verification fails — rejected |
| Valid cert but sends write | Policy engine blocks FC05/06/0F/10 — PLC never sees it |
| Replay attack | TLS session keys are ephemeral — old packet is garbage |

---

## Audit Log Format

```
2026-03-23 14:23:07 - INFO  - [CONNECTED]  127.0.0.1:54821 | Identity: HMI-Client
2026-03-23 14:23:07 - INFO  - [ALLOWED]    HMI-Client | Read Holding Registers FC0x03
2026-03-23 14:23:09 - WARN  - [BLOCKED]    HMI-Client | Write Single Coil FC0x05
2026-03-23 14:23:11 - ERROR - [REJECTED]   127.0.0.1:55003 | SSL Error: no certificate
```
