#!/bin/bash

PATH="$HOME/.local/bin:$PATH"

BSN_CODE=$1

########## 1. Delete Docker Container & Volume and Network Start ##########
docker-compose -f docker-compose.yml -f docker-compose.dev.yml config | 
shyaml keys services | { 
    while read service; 
    do 
    m_c_name="${BSN_CODE}-${service}"
    docker ps | grep $m_c_name
    if [ $? -eq 0 ]; then
        docker stop $m_c_name && docker rm $m_c_name;
    fi 
    done; 
}|| true


docker-compose -f docker-compose.yml -f docker-compose.dev.yml config | 
shyaml keys networks | { 
    while read network; 
    do
    docker network inspect $network
    if [ $? -eq 0 ]; then
        docker network inspect $network | 
        grep Name | 
        grep -v $network | 
        cut -d '"' -f4 | { 
            while read service; 
            do 
            docker stop $service; 
            docker rm $service; 
            done; 
        }; 
        docker network rm $network;
        echo "$network network rm successful"
    else
        echo "$network There is no container connected to the docker network"
    fi
    done; 
}|| true

# docker volume rm $(docker volume ls --filter name=${PWD##*/}_ --format "{{.Name}}") || true
########## 1. Delete Docker Container & Volume and Network End   ##########


########## 2. Docker Build Start    ##########
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d wrapper web serving pp minio postgresql
########## 2. Docker Build End      ##########