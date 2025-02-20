# srsRAN with RIC, grafana and Prometheus $Setup Guide

## Prerequisites
Ensure your system is up to date before proceeding with the installation.

```bash
sudo apt-get update && sudo apt-get upgrade -y

# Install cmake and make
sudo apt-get update
sudo apt-get install -y cmake make

```

## Docker and dependencies Installation

The following script removes any existing Docker installations and installs the latest version along with srsRAN_4G dependencies:

```bash
#!/bin/bash
$
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

# Install Docker and other dependencies for srsUE_4G
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin build-essential cmake libfftw3-dev libmbedtls-dev libboost-program-options-dev libconfig++-dev libsctp-dev libzmq3-dev


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
Then, create the docker network required for the setup:
```bash
docker network create --subnet=10.0.0.0/8 oran-intel
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

### Step 4: Python dependencies
```bash
pip3 install aiohttp influxdb_client aiocsv psutil
```

## Running the Setup

### Terminal 1: Prepare and Start RIC from root directory
```bash
cp -f setup/srsRAN_Project/docker-compose.yml RAN/srsRAN_Project/docker/docker-compose.yml
cp -f setup/srsRAN_Project/open5gs.env RAN/srsRAN_Project/docker/open5gs/open5gs.env
cp -f setup/srsRAN_Project/subscriber_db.csv RAN/srsRAN_Project/docker/open5gs/subscriber_db.csv
cp -f setup/oran-sc-ric/docker-compose.yml RIC/oran-sc-ric/docker-compose.yml
cp -f setup/srsRAN_Project/Dockerfile RAN/srsRAN_Project/docker/Dockerfile
cp -f setup/srsRAN_Project/install_dependencies.sh RAN/srsRAN_Project/docker/scripts/install_dependencies.sh

# Copy srsRAN_Project files which creates RAN Faults

cp -f setup/srsRAN_Project/cu.cpp RAN/srsRAN_Project/apps/cu/cu.cpp
```
<!-- Then, start RIC:
```bash
# Run from O-RAN_srsRAN (Project root directory) after inside screen with name RIC

cd RIC/oran-sc-ric
docker compose up
```

### Terminal 2: Start srsRAN from root directory
```bash
# Run from O-RAN_srsRAN (Project root directory) after inside screen with name RAN

docker compose up
```

### Terminal 3: Start monitoring docker containers tools like Prometheus, Cadvisor, Node-exporter
```bash
# Run from O-RAN_srsRAN (Project root directory)

docker pull prom/prometheus:latest && docker run -d --name=prometheus --network=oran-intel -p 9090:9090 -v=$PWD/setup/prometheus:/prometheus-data prom/prometheus:latest --config.file=/prometheus-data/prometheus.yml

docker pull gcr.io/cadvisor/cadvisor:latest && docker run --name=cadvisor --network=oran-intel --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --publish=8080:8080 --detach=true gcr.io/cadvisor/cadvisor:latest

docker run -d --name=node-exporter --network=oran-intel -p 9100:9100 prom/node-exporter:latest
``` -->

Then, start containerStateChecker/monitor.py
```bash
nohup python3 containerStateChecker/monitor.py > /dev/null 2>&1 &
```


This setup ensures that all required components for RIC and srsRAN are properly installed and running.

