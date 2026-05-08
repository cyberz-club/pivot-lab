Vagrant.configure("2") do |config|
  config.vm.box = "debian/bookworm64"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 512
    vb.cpus = 1
  end

  config.vm.define "attacker" do |attacker|
    attacker.vm.hostname = "attacker"
    attacker.vm.network "private_network", ip: "192.168.56.10"
    attacker.vm.provision "shell", path: "provision/attacker.sh"
  end

  config.vm.define "pivot" do |pivot|
    pivot.vm.hostname = "pivot"
    pivot.vm.network "private_network", ip: "192.168.56.20"
    pivot.vm.network "private_network", ip: "192.168.57.20"
    pivot.vm.provision "shell", path: "provision/pivot.sh"
  end

  config.vm.define "target" do |target|
    target.vm.hostname = "target"
    target.vm.network "private_network", ip: "192.168.57.30"
    target.vm.provision "shell", path: "provision/target.sh"
  end
end
