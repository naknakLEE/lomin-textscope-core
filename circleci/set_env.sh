#!/bin/bash

# docker-compose 파일 변경(컨테이너이름 변경 및 network 변경을 위한 작업)

BSN_CODE=$1

PATH="$HOME/.local/bin:$PATH"

# 1. env 파일 변경
sed -i "s/TEXTSCOPE_BASE_IMAGE_VERSION=0.1.3/TEXTSCOPE_BASE_IMAGE_VERSION=$BSN_CODE/" .env
echo "BSN_CODE=$BSN_CODE" | tee -a .env

# 2. assets config & inference_server config 파일 변경
old_serving_container_name=`yq e '.services.serving.container_name' docker-compose.yml`
new_serving_container_name=${BSN_CODE}-serving
sed -i "s/${old_serving_container_name}/${new_serving_container_name}/g" assets/${BSN_CODE}/pipeline_serving_mapping.json

inference_network=`cat inference_server/assets/conf/config.yaml | shyaml get-value defaults.3.network`
new_minio_container_name=${BSN_CODE}-minio
yq e -i ".minio.host = \"$new_minio_container_name\"" inference_server/assets/conf/network/${inference_network}.yaml

# 3. docker-compose.yml container명 변경
cat docker-compose.yml | shyaml keys services | { 
    while read service; do                     
        m_c_name="${BSN_CODE}-${service}"
        yq e -i ".services.\"$service\".container_name = \"$m_c_name\"" docker-compose.yml
        echo "Success fix ${service} container name to $m_c_name"                
    done; 
}|| true

# 4. docker-compose.yml port바인딩 삭제
yq e -i 'del(.services.*.ports)' docker-compose.yml
yq e -i 'del(.services.*.ports)' docker-compose.dev.yml

yq e -i '.services.wrapper.ports[0] = "9100:${WRAPPER_IP_PORT}"' docker-compose.dev.yml

# 5. network 변경
new_network="${BSN_CODE}-net"
sed -i "s/our_net/$new_network/g" docker-compose.yml
yq e -i ".networks.\"$new_network\".ipam.config[0].subnet = \"172.10.0.0/16\"" docker-compose.yml

# 6. DOCKER SERVER IP ADDRESS 변경
sed -i "s/textscope-/${BSN_CODE}-/g" .env