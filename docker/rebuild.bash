#!/bin/bash

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
