#!/bin/bash

# check for AUTHTOKEN
if [[ -z "${AUTHTOKEN}" ]]; then
  echo "Please set the variable 'AUTHTOKEN' to your access token and use 'sudo -E' to call this script"
  exit
fi

# create data directories
mkdir -p data/cache data/control data/db data/documents data/log/lighttpd
chown www-data:www-data data/log/lighttpd

# cleanup
docker image prune -f
docker container prune -f
docker volume prune -a -f
docker builder prune -a -f

# build
docker compose build --no-cache --pull

# remember GPU passthrough
echo follow https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html to use GPU with docker
