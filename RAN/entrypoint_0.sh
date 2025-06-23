#!/bin/bash

# Add the secondary IP address
ip addr add 175.53.1.11/16 dev eth0

# Execute the provided command (CMD from the Dockerfile)
exec "$@"

