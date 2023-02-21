#!/bin/bash

# docker-compose 파일 변경(컨테이너이름 변경 및 network 변경을 위한 작업)

BSN_CODE=$1

PATH="$HOME/.local/bin:$PATH"

# 1. env 파일 변경
sed -i "s/TEXTSCOPE_BASE_IMAGE_VERSION=0.1.3/TEXTSCOPE_BASE_IMAGE_VERSION=$BSN_CODE/" .env
echo "BSN_CODE=$BSN_CODE" | tee -a .env

# 2. docker-compose.yml container명 변경
fix_container_name_li="wrapper web serving pp"

cat docker-compose.dev.yml | shyaml keys services | { 
    while read service; do 
        if [[ "${fix_container_name_li}" =~ "${service}" ]]; then
            c_name=`cat docker-compose.yml | shyaml get-value services.$service.container_name`
            m_c_name="${c_name}_${BSN_CODE}"
            sed -i "s/container_name: ${c_name}/container_name: ${m_c_name}/" docker-compose.yml
            echo "Success fix container name $c_name to $m_c_name"
        fi            
    done; 
}|| true
# 3. network 변경
sed -i "s/our_net/${BSN_CODE}_net/g" docker-compose.yml
sed -i "s/subnet: 10.254.0.0/subnet: 172.10.0.0/" docker-compose.yml