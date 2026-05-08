#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends python3 python3-flask wget gzip

mkdir -p /opt/pivotapp
cp /vagrant/pivotapp/app.py /opt/pivotapp/app.py

# Note: chisel/ligolo services should NOT be preinstalled or started by provisioning.
# The lab requires the user to exploit the pivot Flask app to install and run the
# tunneling server (ligolo-ng) manually. This keeps the exercise interactive.

cat > /etc/systemd/system/pivotapp.service <<'EOF'
[Unit]
Description=Pivot Flask App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/pivotapp/app.py
WorkingDirectory=/opt/pivotapp
Restart=on-failure
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pivotapp.service
systemctl restart pivotapp.service
