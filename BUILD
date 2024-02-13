local_environment(
    name="local_linux",
    compatible_platforms=["linux_arm64", "linux_x86_64"],
    fallback_environment="linux_docker",
)

local_environment(
    name="local_macos",
    compatible_platforms=["macos_arm64", "macos_x86_64"],
)

# We deploy to Linux instances
docker_environment(
    name="docker_bookworm",
    platform="linux_x86_64",
    image="python:3.11-slim-bookworm",
)
