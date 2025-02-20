import subprocess
import time
from datetime import datetime
import sys
import subprocess


# Define the screen command to reattach to the 'RAN' session and send commands
commands = [
    "screen -r OTHERS -X 'ps aux | grep 'stresser.py' | awk '{print $2}' | xargs kill\n'",
    "screen -r OTHERS -X 'ps aux | grep 'trafficGenerator.py' | awk '{print $2}' | xargs kill\n'",
    "screen -r OTHERS -X 'ps aux | grep 'dataScrapper.py' | awk '{print $2}' | xargs kill\n'",
    "screen -r RAN -X stuff 'docker compose down\n'",  # Run docker compose down RAN
    "screen -r RAN -X stuff 'docker compose up\n'",     # Run docker compose up RAN
    "screen -r RIC -X stuff 'docker compose down\n'",  # Run docker compose down RIC
    "screen -r RIC -X stuff 'docker compose up\n'",     # Run docker compose up RIC
    "screen -r MON -X stuff 'docker rm -f prometheus cadvisor node-exporter\n'",
    "screen -r MON -X stuff 'docker pull prom/prometheus:latest && docker run -d --name=prometheus --network=oran-intel -p 9090:9090 -v=$PWD/setup/prometheus:/prometheus-data prom/prometheus:latest --config.file=/prometheus-data/prometheus.yml && docker pull gcr.io/cadvisor/cadvisor:latest && docker run --name=cadvisor --network=oran-intel --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --publish=8080:8080 --detach=true gcr.io/cadvisor/cadvisor:latest && docker run -d --name=node-exporter --network=oran-intel -p 9100:9100 prom/node-exporter:latest\n'",
    "screen -r OTHERS -X 'python3 stresser/stresser.py &\n'",
    "screen -r OTHERS -X 'python3 trafficGenerator/trafficGenerator.py &\n'",
    "screen -r OTHERS -X 'python3 dataScrapper/dataScrapper.py &\n'",
]
    
def monitor_containers():
    containers_to_check = ["srscu0", "srscu1", "srscu2", "srscu3", "srsdu3", "srsdu2", "srsdu1", "srsdu0"]
    containers_to_check_logs = ["srsue0", "srsue1", "srsue2", "srsue3"]
    log_keyword = "Received RRC Release"

    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            # Verify containers are running using docker ps
            running_containers = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"], text=True).splitlines()
            # print(running_containers)
            for container_name in containers_to_check:
                if container_name not in running_containers:
                    print(f"{timestamp} WARNING: Container '{container_name}' is not running.")
                    # Execute the commands in sequence
                    for command in commands:
                        result = subprocess.run(command, capture_output=True, text=True, shell=True)
                    # return
            for container_name in containers_to_check_logs:
                if container_name in running_containers:
                    try:
                        logs = subprocess.check_output(["docker", "logs", "--tail", "50", container_name], text=True)
                        if log_keyword in logs:
                            print(f"{timestamp} WARNING: Found '{log_keyword}' in logs of container '{container_name}'.")
                            # Execute the commands in sequence
                            for command in commands:
                                result = subprocess.run(command, capture_output=True, text=True, shell=True)
                            # return
                    except subprocess.CalledProcessError:
                        print(f"{timestamp} WARNING: Failed to retrieve logs for container '{container_name}'.")
                        # Execute the commands in sequence
                        for command in commands:
                            result = subprocess.run(command, capture_output=True, text=True, shell=True)
                        # return
        except Exception as e:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} An error occurred: {e}")
            # Execute the commands in sequence
            for command in commands:
                result = subprocess.run(command, capture_output=True, text=True, shell=True)
            # return
        time.sleep(1)

if __name__ == "__main__":
    monitor_containers()
