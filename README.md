# srsRAN with RIC, grafana adSetup Guide

## Prerequisites
Ensure your system is up to date before proceeding with the installation.

```bash
sudo apt-get update && sudo apt-get upgrade -y

# Install cmake and make
sudo apt-get update
sudo apt-get install -y cmake make

```

## Docker Installation

The following script removes any existing Docker installations and installs the latest version:

```bash
#!/bin/bash

# Remove existing Docker packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    sudo apt-get remove -y $pkg;
done

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin build-essential cmake libfftw3-dev libmbedtls-dev libboost-program-options-dev libconfig++-dev libsctp-dev


# Verify Docker installation
sudo docker run hello-world

# Add user to Docker group
sudo groupadd docker
sudo usermod -aG docker $USER

# Enable Docker services
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

To apply the group changes, either reboot or run:
```bash
newgrp docker
```
Then, verify Docker runs without sudo:
```bash
docker run hello-world
```

## Cloning and Setting Up srsRAN

### Step 1: Clone the srsRAN Project Repository and checkout
```bash
cd RAN
git clone https://github.com/srsran/srsRAN_Project.git
cd srsRAN_Project
git checkout e5d5b44
cd ../..
```

### Step 2: Build UE
```bash
cd UE/
git clone https://github.com/srsran/srsRAN_4G.git
cd srsRAN_4G
mkdir build
cd build
cmake ../
make -j$(nproc)
cd ../../../
```

### Step 3: Clone and Set Up RIC
```bash
mkdir -p RIC
cd RIC/
git clone https://github.com/srsran/oran-sc-ric.git
cd ../
```

## Running the Setup

### Terminal 1: Prepare and Start RIC from root directory
```bash
cp -f setup/srsRAN_Project/docker-compose.yml RAN/srsRAN_Project/docker/
cp -f setup/srsRAN_Project/open5gs.env RAN/srsRAN_Project/docker/open5gs
cp -f setup/srsRAN_Project/subscriber_db.csv RAN/srsRAN_Project/docker/open5gs
cp -f setup/oran-sc-ric/docker-compose.yml RIC/oran-sc-ric/

```
Then, start RIC:
```bash
cd RIC/oran-sc-ric
docker compose up
```

### Terminal 2: Start srsRAN from root directory
```bash
docker compose up
```

This setup ensures that all required components for RIC and srsRAN are properly installed and running.

