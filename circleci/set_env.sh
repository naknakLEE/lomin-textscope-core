#!/bin/bash

# docker-compose 파일 변경(컨테이너이름 변경 및 network 변경을 위한 작업)

BSN_CODE=$1

# 1. env 파일 변경
sed -i "s/TEXTSCOPE_BASE_IMAGE_VERSION=0.1.3/TEXTSCOPE_BASE_IMAGE_VERSION=$BSN_CODE" .env
echo "BSN_CODE=$BSN_CODE" | tee -a .env

# 2. docker-compsoe.yml container명 변경
s_list=`cat docker-compose.yml | shyaml keys services`
for service in $s_list; do
    c_name=`cat docker-compose.yml | shyaml keys services.$service.container_name`
    echo "Fix container name $container_name"
    m_c_name="${c_name}_${BSN_CODE}"
    sed -i "s/container_name: ${c_name}/container_name: ${m_c_name}" docker-compsoe.yml
done

# 3. network 변경
sed -i "s/our_net/${BSN_CODE}_net/g" docker-compsoe.yml
sed -i "s|subnet: 10.254.0.0|subnet: 172.10.0.0" docker-compose.yml