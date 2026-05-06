Vagrant.configure("2") do |config|

  # ----------------------------
  # VM1 - Attacker (Kali Linux)
  # ----------------------------
  config.vm.define "attacker" do |attacker|
    attacker.vm.box = "kalilinux/rolling"
    attacker.vm.hostname = "attacker"

    # Internet-facing network (can reach pivot)
    attacker.vm.network "private_network", ip: "10.0.0.10", virtualbox__intnet: "internet-net"

    attacker.vm.provider "virtualbox" do |vb|
      vb.name   = "attacker"
      vb.memory = 2048
      vb.cpus   = 2
    end

    attacker.vm.provision "shell", inline: <<-SHELL
      echo "[*] Setting up Attacker machine..."

      # Update and install essentials
      apt-get update -qq
      apt-get install -y -qq proxychains4 curl wget git python3 python3-pip net-tools

      # Download Chisel (attacker side = client)
      CHISEL_VERSION="1.9.1"
      wget -q "https://github.com/jpillora/chisel/releases/download/v${CHISEL_VERSION}/chisel_${CHISEL_VERSION}_linux_amd64.gz" -O /tmp/chisel.gz
      gunzip /tmp/chisel.gz
      mv /tmp/chisel /usr/local/bin/chisel
      chmod +x /usr/local/bin/chisel

      # Download Ligolo-ng proxy (runs on attacker)
      LIGOLO_VERSION="0.6.2"
      wget -q "https://github.com/nicocha30/ligolo-ng/releases/download/v${LIGOLO_VERSION}/ligolo-ng_proxy_${LIGOLO_VERSION}_linux_amd64.tar.gz" -O /tmp/ligolo-proxy.tar.gz
      tar -xzf /tmp/ligolo-proxy.tar.gz -C /tmp/
      mv /tmp/proxy /usr/local/bin/ligolo-proxy
      chmod +x /usr/local/bin/ligolo-proxy

      # Configure proxychains to use SOCKS5 on 1080
      cat > /etc/proxychains4.conf <<'EOF'
strict_chain
proxy_dns
[ProxyList]
socks5 127.0.0.1 1080
EOF

      # Add route so attacker knows internal net goes through pivot
      # (only needed for Ligolo — Ligolo will create a tun interface)
      echo "[*] Attacker ready. IP: 10.0.0.10"
    SHELL
  end

  # ----------------------------
  # VM2 - Pivot (Ubuntu 22.04)
  # ----------------------------
  config.vm.define "pivot" do |pivot|
    pivot.vm.box = "ubuntu/jammy64"
    pivot.vm.hostname = "pivot"

    # Internet-facing NIC (attacker can reach this)
    pivot.vm.network "private_network", ip: "10.0.0.20",       virtualbox__intnet: "internet-net"

    # Internal NIC (can reach target, attacker cannot)
    pivot.vm.network "private_network", ip: "192.168.100.20",  virtualbox__intnet: "internal-net"

    pivot.vm.provider "virtualbox" do |vb|
      vb.name   = "pivot"
      vb.memory = 1024
      vb.cpus   = 1
    end

    pivot.vm.provision "shell", inline: <<-SHELL
      echo "[*] Setting up Pivot machine..."

      apt-get update -qq
      apt-get install -y -qq python3 python3-pip python3-flask net-tools curl

      # Copy Flask vulnerable app
      cp /vagrant/vm2-pivot/app.py /opt/vuln-app.py
      cp -r /vagrant/vm2-pivot/templates /opt/templates

      # Create systemd service for the Flask app
      cat > /etc/systemd/system/vuln-app.service <<'EOF'
[Unit]
Description=Vulnerable Flask App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/vuln-app.py
WorkingDirectory=/opt
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

      systemctl daemon-reload
      systemctl enable vuln-app
      systemctl start vuln-app

      echo "[*] Pivot ready. Internet IP: 10.0.0.20 | Internal IP: 192.168.100.20"
    SHELL
  end

  # ----------------------------
  # VM3 - Target (Ubuntu 22.04)
  # ----------------------------
  config.vm.define "target" do |target|
    target.vm.box = "ubuntu/jammy64"
    target.vm.hostname = "target"

    # Internal network only — attacker CANNOT reach this directly
    target.vm.network "private_network", ip: "192.168.100.30", virtualbox__intnet: "internal-net"

    target.vm.provider "virtualbox" do |vb|
      vb.name   = "target"
      vb.memory = 1024
      vb.cpus   = 1
    end

    target.vm.provision "shell", inline: <<-SHELL
      echo "[*] Setting up Target machine..."

      apt-get update -qq
      apt-get install -y -qq python3 python3-pip python3-flask openssh-server net-tools

      # Copy internal Flask app
      cp /vagrant/vm3-target/internal_app.py /opt/internal-app.py
      cp -r /vagrant/vm3-target/templates /opt/internal-templates

      # Create systemd service for internal app
      cat > /etc/systemd/system/internal-app.service <<'EOF'
[Unit]
Description=Internal Secret Flask App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/internal-app.py
WorkingDirectory=/opt
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

      systemctl daemon-reload
      systemctl enable internal-app
      systemctl start internal-app

      # Setup SSH with a known user for the demo
      useradd -m -s /bin/bash secretuser
      echo "secretuser:password123" | chpasswd

      # Allow password auth in SSH (disabled by default on Ubuntu)
      sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
      sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/'   /etc/ssh/sshd_config
      systemctl restart ssh

      echo "[*] Target ready. Internal IP: 192.168.100.30"
      echo "[*] SSH user: secretuser / password123"
    SHELL
  end

end
