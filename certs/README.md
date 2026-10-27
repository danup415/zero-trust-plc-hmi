# Certs — Certificate Infrastructure

This folder contains the script to generate all certificates needed for
mutual TLS (mTLS) authentication between the ZT proxy and HMI.

**⚠️ IMPORTANT: Never commit real private keys to git.**
The `.gitignore` file excludes all `.key`, `.crt`, `.csr`, `.pem`, and `.srl` files.
Only `generate_certs.sh` is committed.

---

## What Gets Generated

| File | Type | Purpose |
|---|---|---|
| `ca.key` | CA private key | Root of trust — keep secure |
| `ca.crt` | CA certificate | Trusted by all components |
| `plc.key` | Server private key | Identity of ZT proxy |
| `plc.crt` | Server certificate | Signed by CA, presented to HMI |
| `hmi.key` | Client private key | Identity of HMI |
| `hmi.crt` | Client certificate | Signed by CA, presented to proxy |

---

## How to Generate

```bash
chmod +x certs/generate_certs.sh
./certs/generate_certs.sh
```

Expected output:
```
[1/5] Generating Certificate Authority...
[2/5] Generating PLC Server certificate...
[3/5] Generating HMI Client certificate...
[4/5] Verifying certificates...
plc.crt: OK
hmi.crt: OK
[5/5] Done! Certificates created in ./certs/
```

---

## How mTLS Works (Simple)

```
CA signs both certificates
        │
        ├── Signs plc.crt  (given to ZT proxy)
        └── Signs hmi.crt  (given to HMI client)

When HMI connects to proxy:
  HMI  → "Here is my hmi.crt"
  Proxy → verifies signature against ca.crt ✓
  Proxy → "Here is my plc.crt"
  HMI  → verifies signature against ca.crt ✓
  Both verified → connection allowed
```

---

## Regenerating Certificates

If you see SSL errors, regenerate:

```bash
rm -f certs/*.key certs/*.crt certs/*.csr certs/*.srl
./certs/generate_certs.sh
```
