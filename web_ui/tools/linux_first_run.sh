#!/bin/bash

python3 -m pip install pymongo
python3 init_mongo_scheme.py

docker pull mongo
../swarm/deploy.sh

cd ../web_ui/application/app/bcomponents/parser_backend/isolated_env
./build_docker_image.sh

