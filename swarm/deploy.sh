#!/bin/bash

#(cd ../server; ./build_image.sh)

docker stack deploy -c euclid.yml euclid
