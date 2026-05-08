Vagrant.configure("2") do |config|
  config.vm.box = "debian/bookworm64"
  # ensure project root is synced into guests at /vagrant
  config.vm.synced_folder ".", "/vagrant", type: "virtualbox"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 512
    vb.cpus = 1
  end

  config.vm.define "attacker" do |attacker|
    attacker.vm.hostname = "attacker"
    attacker.vm.network "private_network", ip: "192.168.56.10", netmask: "255.255.255.0"
    attacker.vm.provision "shell", path: "provision/attacker.sh"
  end

  config.vm.define "pivot" do |pivot|
    pivot.vm.hostname = "pivot"
    # attacker-facing host-only network
    pivot.vm.network "private_network", ip: "192.168.56.20", netmask: "255.255.255.0"

    # target-facing isolated network (VirtualBox internal network, not reachable from attacker)
    pivot.vm.network "private_network",
      ip: "192.168.57.20",
      netmask: "255.255.255.0",
      virtualbox__intnet: "pivot-target"
    pivot.vm.provision "shell", path: "provision/pivot.sh"
  end

  config.vm.define "target" do |target|
    target.vm.hostname = "target"
    target.vm.network "private_network",
      ip: "192.168.57.30",
      netmask: "255.255.255.0",
      virtualbox__intnet: "pivot-target"
    target.vm.provision "shell", path: "provision/target.sh"
  end
end
