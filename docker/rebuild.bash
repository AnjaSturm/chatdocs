#!/bin/bash

# stop
docker compose down

# cleanup
docker rm `sudo docker ps -a | awk '/^[0-9a-f]/ {print $1}'`
docker rmi `sudo docker images | awk '/<none>/ {print $3}'`
docker volume prune -f

# build
docker compose build --no-cache --pull

# start
docker compose up -d
