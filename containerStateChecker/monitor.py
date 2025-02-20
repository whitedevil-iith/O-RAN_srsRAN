import subprocess
import time
import psutil
import signal
import sys
from datetime import datetime

# Define process names and containers to manage
processes_to_kill = ["stresser.py", "trafficGenerator.py", "dataScrapper.py"]
containers_to_check = ["srscu0", "srscu1", "srscu2", "srscu3", "srsdu3", "srsdu2", "srsdu1", "srsdu0"]
containers_to_check_logs = ["srsue0", "srsue1", "srsue2", "srsue3"]
log_keyword = "Received RRC Release"

# Kill a process by name
def kill_processes():
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            for pname in processes_to_kill:
                if proc.info['cmdline'] and pname in " ".join(proc.info['cmdline']):
                    print(f"Killing process: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

# Stop all running containers
def stop_containers():
    print("Stopping all running containers...")
    subprocess.run("docker stop $(docker ps -q)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("docker rm $(docker ps -aq)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Start processes
def start_processes():
    print("Starting Python scripts...")
    subprocess.Popen(["python3", "stresser/stresser.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["python3", "trafficGenerator/trafficGenerator.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["python3", "dataScrapper/dataScrapper.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Restart Docker services
def restart_services():
    print("Restarting RIC and RAN...")
    subprocess.run("cd /home/newsl/workspace/O-RAN_srsRAN/RIC/oran-sc-ric && docker compose up -d", shell=True)
    subprocess.run("cd /home/newsl/workspace/O-RAN_srsRAN && docker compose up -d", shell=True)

# Restart monitoring services
def restart_monitoring():
    print("Restarting monitoring services...")
    subprocess.run("docker rm -f prometheus cadvisor node-exporter", shell=True)
    subprocess.run(
        "docker pull prom/prometheus:latest && docker run -d --name=prometheus --network=oran-intel -p 9090:9090 "
        "-v=$PWD/setup/prometheus:/prometheus-data prom/prometheus:latest --config.file=/prometheus-data/prometheus.yml",
        shell=True
    )
    subprocess.run(
        "docker pull gcr.io/cadvisor/cadvisor:latest && docker run --name=cadvisor --network=oran-intel "
        "--volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro "
        "--publish=8080:8080 --detach=true gcr.io/cadvisor/cadvisor:latest",
        shell=True
    )
    subprocess.run(
        "docker run -d --name=node-exporter --network=oran-intel -p 9100:9100 prom/node-exporter:latest",
        shell=True
    )

# Cleanup function on exit
def cleanup(signal_received=None, frame=None):
    print("\nReceived termination signal. Cleaning up...")
    kill_processes()
    stop_containers()
    print("Cleanup complete. Exiting.")
    sys.exit(0)

# Handle termination signals (Ctrl+C, kill)
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# Check container health
def check_containers():
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        try:
            running_containers = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"], text=True).splitlines()

            for container_name in containers_to_check:
                if container_name not in running_containers:
                    print(f"{timestamp} WARNING: Container '{container_name}' is not running. Restarting services...")
                    restart_services()
                    kill_processes()
                    start_processes()

            for container_name in containers_to_check_logs:
                if container_name in running_containers:
                    try:
                        logs = subprocess.check_output(["docker", "logs", "--tail", "50", container_name], text=True)
                        if log_keyword in logs:
                            print(f"{timestamp} WARNING: Found '{log_keyword}' in logs of container '{container_name}'. Restarting services...")
                            restart_services()
                            kill_processes()
                            start_processes()
                    except subprocess.CalledProcessError:
                        print(f"{timestamp} WARNING: Failed to retrieve logs for container '{container_name}'. Restarting services...")
                        restart_services()
                        kill_processes()
                        start_processes()

        except Exception as e:
            print(f"{timestamp} ERROR: {e}. Restarting services...")
            restart_services()
            kill_processes()
            start_processes()
        
        time.sleep(3)

if __name__ == "__main__":
    print("Starting monitoring system...")
    kill_processes()  # Ensure no duplicate processes exist
    restart_services()  # Restart network services
    restart_monitoring()  # Restart monitoring stack
    start_processes()  # Start Python scripts
    check_containers()  # Start container monitoring
