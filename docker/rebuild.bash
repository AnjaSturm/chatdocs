#!/bin/bash

if [[ -z "${AUTHTOKEN}" ]]; then
  echo "Please set the variable 'AUTHTOKEN' to your access token and use 'sudo -E' to call this script"
  exit
fi

# stop
./stop.bash

# cleanup
docker image prune -f
docker container prune -f
docker volume prune -a -f
docker builder prune -a -f

# build
docker compose build --no-cache --pull

# start
./start.bash
