#!/bin/bash

service docker start
cd ./app/bcomponents/parser_backend/isolated_env
./build_docker_image.sh
cd /app
python init_mongo_scheme.py
python manage.py runserver

