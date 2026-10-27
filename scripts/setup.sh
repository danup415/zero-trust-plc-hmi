#!/bin/bash
echo "======================================"
echo " Zero Trust PLC-HMI — Setup Script"
echo "======================================"

echo "[1] Updating system..."
sudo apt update -y

echo "[2] Installing system dependencies..."
sudo apt install -y git curl openssl wireshark net-tools nodejs npm python3-pip

echo "[3] Installing Python packages..."
pip install pymodbus==3.6.9 websockets scapy --break-system-packages

echo "[4] Installing Node-RED..."
sudo npm install -g --unsafe-perm node-red

echo "[5] Installing Node-RED palettes..."
cd ~/.node-red
npm install node-red-contrib-modbus node-red-dashboard

echo "[6] Cloning OpenPLC Runtime..."
cd ~
git clone https://github.com/thiagoralves/OpenPLC_v3.git
cd OpenPLC_v3
./install.sh linux

echo "[7] Generating certificates..."
cd ~/zero-trust-plc-hmi
chmod +x certs/generate_certs.sh
./certs/generate_certs.sh

echo "======================================"
echo " Setup complete!"
echo " Run: ~/scripts/start_plc.sh"
echo "======================================"
