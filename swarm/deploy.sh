#!/bin/bash

(cd ../web_ui; ./docker_build.sh)

docker stack deploy -c euclid.yml euclid
