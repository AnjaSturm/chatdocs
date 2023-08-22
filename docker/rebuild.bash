#!/bin/bash

# stop
docker compose down

# cleanup
docker image prune -f
docker container prune -f
docker volume prune -a -f
docker builder prune -a -f

# build
docker compose build --no-cache --pull

# start
docker compose up -d
