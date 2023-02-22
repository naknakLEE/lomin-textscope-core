#!/bin/bash

# docker-compose 파일 변경(컨테이너이름 변경 및 network 변경을 위한 작업)

BSN_CODE=$1

PATH="$HOME/.local/bin:$PATH"

# 1. env 파일 변경
sed -i "s/TEXTSCOPE_BASE_IMAGE_VERSION=0.1.3/TEXTSCOPE_BASE_IMAGE_VERSION=$BSN_CODE/" .env
echo "BSN_CODE=$BSN_CODE" | tee -a .env

# 2. docker-compose.yml container명 변경
cat docker-compose.yml | shyaml keys services | { 
    while read service; do                     
        m_c_name="${BSN_CODE}_${service}"
        yq e -i ".services.\"$service\".container_name = \"$m_c_name\"" docker-compose.yml
        echo "Success fix ${service} container name to $m_c_name"                
    done; 
}|| true

# 3. docker-compose.yml port바인딩 삭제
yq e -i 'del(.services.*.ports)' docker-compose.yml

# 4. docker-compose.dev.yml wrapper,web,serving,pp port 바인딩 변경
yq e -i '.services.wrapper.ports[0] = "10080:${WRAPPER_IP_PORT}"' docker-compose.dev.yml
yq e -i '.services.web.ports[0] = "10081:${WEB_IP_PORT}"' docker-compose.dev.yml
yq e -i '.services.serving.ports[0] = "10082:${SERVING_IP_PORT}"' docker-compose.dev.yml
yq e -i '.services.pp.ports[0] = "10083:${PP_IP_PORT}"' docker-compose.dev.yml

# 5. network 변경
new_network="${BSN_CODE}_net"
sed -i "s/our_net/$new_network/g" docker-compose.yml
yq e -i ".networks.\"$new_network\".ipam.config[0].subnet = \"172.10.0.0/16\"" docker-compose.yml