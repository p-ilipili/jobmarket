#!/bin/bash

# Check if a network exists and create it if it doesn't
network_name="jm_network"
if ! docker network ls | grep -q "$network_name"; then
  echo "Creating Docker network: $network_name"
  docker network create --driver bridge "$network_name"
else
  echo "Network $network_name already exists."
fi