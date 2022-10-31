#!/bin/bash

set -eux

docker-compose -f ./docker-compose.prod.yml build

mkdir ./front_build

docker save docker.lomin.ai/ts-plugin-webview | pigz -6 > ./front_build/ts-plugin-webview.tar.gz
echo `md5sum ./front_build/ts-plugin-webview.tar.gz` >> "./front_build/checksum(md5).txt"
