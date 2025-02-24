import subprocess
import time
import psutil
import signal
import sys
from datetime import datetime

# Define processes and containers to manage
# processes_to_monitor = ["stresser/stresser.py", "trafficGenerator/trafficGenerator.py"]
processes_to_monitor = ["stresser/final_stresser_&_data_Scrapper.py", "trafficGenerator/trafficGenerator.py"]
containers_to_check = ["srscu0", "srscu1", "srscu2", "srscu3", "srsdu3", "srsdu2", "srsdu1", "srsdu0"]
containers_to_check_logs = ["srsue0", "srsue1", "srsue2", "srsue3"]
log_keyword = "Received RRC Release"

# Kill all specified processes
def kill_processes():
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        try:
            if proc.info['cmdline']:
                for pname in processes_to_monitor:
                    if pname in " ".join(proc.info['cmdline']):
                        print(f"Killing process: {proc.info['cmdline']} (PID: {proc.info['pid']})")
                        proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

# Stop all running containers
def stop_containers():
    print("Stopping all running containers...")
    subprocess.run("docker stop $(docker ps -q)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("docker rm $(docker ps -aq)", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Start processes if they are not running
def start_processes():
    print("Ensuring all required Python scripts are running...")
    running_processes = []

    # Get currently running processes
    for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
        try:
            if proc.info['cmdline']:  # Avoid empty cmdline cases
                running_processes.append(" ".join(proc.info['cmdline']))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    for script in processes_to_monitor:
        script_found = any(script in cmd for cmd in running_processes)
        
        if not script_found:
            print(f"Starting process: {script}")
            subprocess.Popen(["python3", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    subprocess.run("docker run -d --name=node-exporter --network=oran-intel -p 9100:9100 prom/node-exporter:latest", shell=True)

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

# Check container and process health
def check_system_health():
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        try:
            # Check running containers
            running_containers = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"], text=True).splitlines()
            for container_name in containers_to_check:
                if container_name not in running_containers:
                    print(f"{timestamp} WARNING: Container '{container_name}' is not running. Restarting it...")
                    subprocess.run(f"docker start {container_name}", shell=True)

            # Check container logs for errors
            for container_name in containers_to_check_logs:
                if container_name in running_containers:
                    logs = subprocess.check_output(["docker", "logs", "--tail", "50", container_name], text=True)
                    if log_keyword in logs:
                        print(f"{timestamp} WARNING: Found '{log_keyword}' in logs of container '{container_name}'. Restarting services...")
                        kill_processes()
                        restart_services()
                        start_processes()

            # Ensure processes are running correctly
            running_processes = []
            for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        running_processes.append(" ".join(proc.info['cmdline']))  # Store full command line
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            for script in processes_to_monitor:
                script_found = any(script in cmd for cmd in running_processes)
                
                if not script_found:
                    print(f"{timestamp} WARNING: Process '{script}' is not running. Restarting it...")
                    subprocess.Popen(["python3", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        except Exception as e:
            print(f"{timestamp} ERROR: {e}. Restarting services...")
            kill_processes()
            restart_services()
            start_processes()

        time.sleep(3)

if __name__ == "__main__":
    print("Starting monitoring system...")  
    kill_processes()  # Ensure no duplicate processes exist
    restart_services()  # Restart network services
    restart_monitoring()  # Restart monitoring stack
    start_processes()  # Ensure required Python scripts are running
    check_system_health()  # Start system monitoring
