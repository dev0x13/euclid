#!/bin/bash

version='latest'

docker build \
    --build-arg version=$version \
    -t euclid-web-ui:$version \
    -f Dockerfile .

