import subprocess
import time
from datetime import datetime
import sys
import subprocess


# Define the screen command to reattach to the 'RAN' session and send commands
commands = [
    "screen -r RAN -X stuff 'docker compose down\n'",  # Run docker compose down
    "screen -r RAN -X stuff 'docker compose up\n'"     # Run docker compose up
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
