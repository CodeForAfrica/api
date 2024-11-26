# Pesacheck Meedan Bridge

A simple service to pull articles from PesaCheck and post them to Meedan Check using Meedan Graphql API. This service acts as a bridge between PesaCheck and Meedan Check, allowing for seamless transfer of articles from one platform to another.

## Getting Started

First create `.env` file in the app directory. From project root directory,

```sh
cp  pesacheck_meedan_bridge/.env.example pesacheck_meedan_bridge/.env
```

and modify the `.env` file according to your needs.

## Build

To build a `pex` binary, run:

```sh
pants package pesacheck_meedan_bridge/py:pesacheck_meedan_bridge
```

To build the docker image, run:

```sh
VERSION=$(cat pesacheck_meedan_bridge/py/VERSION) pants package pesacheck_meedan_bridge/docker:pesacheck_meedan_bridge
```

## Run

To run the built docker image, execute:

```sh
docker compose --env-file ./pesacheck_meedan_bridge/.env up pesacheck_meedan_bridge
```
To get container ID of this script, execute:
```sh
container_id=$(docker ps --filter "ancestor=codeforafrica/pesacheck_meedan_bridge:latest" --format "{{.ID}}" | head -n 1) && [ -z "$container_id" ] && echo "No running container found for the image codeforafrica/pesacheck_meedan_bridge:latest"
```
To run `pex` binary, execute:

```sh
docker exec -it $container_id ./pex
```
