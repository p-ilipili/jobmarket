#!/bin/bash

# Redirect all output to log.txt
exec > ./log/run_log.txt 2>&1
echo "Starting setup script..."

# Go to the directory where the docker-compose.yml file is located
cd "$(dirname "$0")/docker_init" || { echo "Failed to navigate to docker_init"; exit 1; }

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start or rebuild the containers using docker-compose
echo "Starting containers using Docker Compose..."
docker-compose up -d --build

# Optionally, tail logs to view container output (if you want to do that in the same script)
# docker-compose logs -f

echo "Docker Compose setup completed."