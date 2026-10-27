#!/bin/bash
echo "Killing existing instances..."
sudo fuser -k 8080/tcp
sudo fuser -k 8443/tcp
sudo fuser -k 502/tcp
echo "Waiting for ports to free..."
sleep 5
echo "Setting capabilities..."
sudo setcap cap_net_bind_service=+ep /home/anup/OpenPLC_v3/webserver/core/openplc
echo "Starting OpenPLC as root..."
cd ~/OpenPLC_v3
sudo ./start_openplc.sh
