#!/bin/bash

version='0.1'

docker build \
    --build-arg version=$version \
    -t euclid-web-ui:$version  \
    -f ../Dockerfile .

