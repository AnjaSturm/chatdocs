#!/bin/bash

# create data directories
mkdir -p datae/cache data/control data/db data/documents data/log

# cleanup
docker image prune -f
docker container prune -f
docker volume prune -a -f
docker builder prune -a -f

# build
docker compose build --no-cache --pull

# remember GPU passthrough
echo follow https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html to use GPU with docker
