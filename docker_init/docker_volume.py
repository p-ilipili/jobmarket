from docker import DockerClient

def create_docker_volume(volume_name, host_path):
    """Create a Docker volume and bind it to a host path using Docker SDK."""
    client = DockerClient()

    # Create the volume with the specified driver and options
    volume = client.volumes.create(
        volume_name,
        driver="local",
        driver_opts={
            "type": "none",
            "device": host_path,
            "o": "bind"
        }
    )

    print(f"Docker volume '{volume_name}' created successfully and mapped to '{host_path}'.")

# Define the volume name and host path
volume_name = "working_dir"
host_path = "/Volumes/Data/dev/jobmarket_global/docker_vol"  # Replace with the desired directory on the host

# Create the volume
create_docker_volume(volume_name, host_path)