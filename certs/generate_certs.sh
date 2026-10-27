#!/bin/bash
# Zero Trust PKI — generates CA, PLC, and HMI certificates
# Run once before starting the system

mkdir -p certs
cd certs

echo "[1/5] Generating Certificate Authority..."
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/CN=WaterTank-CA/O=ZeroTrust-Lab/C=IN"

echo "[2/5] Generating PLC Server certificate..."
openssl genrsa -out plc.key 2048
openssl req -new -key plc.key -out plc.csr \
  -subj "/CN=PLC-Server/O=ZeroTrust-Lab/C=IN"
openssl x509 -req -days 3650 -in plc.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial -out plc.crt

echo "[3/5] Generating HMI Client certificate..."
openssl genrsa -out hmi.key 2048
openssl req -new -key hmi.key -out hmi.csr \
  -subj "/CN=HMI-Client/O=ZeroTrust-Lab/C=IN"
openssl x509 -req -days 3650 -in hmi.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial -out hmi.crt

echo "[4/5] Verifying certificates..."
openssl verify -CAfile ca.crt plc.crt
openssl verify -CAfile ca.crt hmi.crt

echo "[5/5] Done! Certificates created in ./certs/"
echo "CA:  certs/ca.crt"
echo "PLC: certs/plc.crt + plc.key"
echo "HMI: certs/hmi.crt + hmi.key"
