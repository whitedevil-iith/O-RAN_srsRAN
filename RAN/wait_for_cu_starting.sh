#!/bin/bash
# Parameters: $1 is the container name, $2 is the log string to search for
CONTAINER_NAME=$1
LOG_STRING=$2

# Loop until the log string is found in the container's logs
while true; do
  if docker logs "$CONTAINER_NAME" 2>&1 | grep -q "$LOG_STRING"; then
    echo "Log message '$LOG_STRING' found in $CONTAINER_NAME logs. Proceeding..."
    break
  fi
  echo "Waiting for log message '$LOG_STRING'..."
  sleep 2  # Wait for 2 seconds before checking again
done
