#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends python3 python3-flask wget gzip
mkdir -p /opt/pivotapp
cp /vagrant/pivotapp/app.py /opt/pivotapp/app.py

CHISEL_VERSION="1.8.1"
CHISEL_URL="https://github.com/jpillora/chisel/releases/download/v${CHISEL_VERSION}/chisel_${CHISEL_VERSION}_linux_amd64.gz"
mkdir -p /usr/local/bin
wget -qO- "$CHISEL_URL" | gunzip > /usr/local/bin/chisel
chmod +x /usr/local/bin/chisel

cat > /etc/systemd/system/pivotapp.service <<'EOF'
[Unit]
Description=Pivot Flask App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/pivotapp/app.py
WorkingDirectory=/opt/pivotapp
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pivotapp.service
systemctl restart pivotapp.service
