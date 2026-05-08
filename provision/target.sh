#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends python3 python3-flask sqlite3
mkdir -p /opt/targetapp
cp /vagrant/targetapp/app.py /opt/targetapp/app.py
cp /vagrant/targetapp/init_db.py /opt/targetapp/init_db.py
python3 /opt/targetapp/init_db.py

cat > /etc/systemd/system/targetapp.service <<'EOF'
[Unit]
Description=Target Flask App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/targetapp/app.py
WorkingDirectory=/opt/targetapp
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable targetapp.service
systemctl restart targetapp.service
