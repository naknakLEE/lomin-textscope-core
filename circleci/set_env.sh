#!/bin/bash

BSN_CODE=$1

PATH="$HOME/.local/bin:$PATH"

# 1. env 파일 변경
# sed -i '/^TEXTSCOPE_.*VERSION=/s/=.*/='$BSN_CODE'/g' .env
sed -i '/^BSN_CODE=/ s/=.*/='$BSN_CODE'/' .env

# 2. assets config & inference_server config 파일 변경
old_serving_container_name=`yq e '.services.serving.container_name' docker-compose.yml`
new_serving_container_name=${BSN_CODE}-serving
sed -i "s/${old_serving_container_name}/${new_serving_container_name}/g" assets/${BSN_CODE}/pipeline_serving_mapping.json

inference_network=`cat inference_server/assets/conf/config.yaml | shyaml get-value defaults.3.network`
new_minio_container_name=${BSN_CODE}-minio
yq e -i ".minio.host = \"$new_minio_container_name\"" inference_server/assets/conf/network/${inference_network}.yaml

sed -i "s/ --reload//" inference_server/assets/run-dev.sh

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

yq e -i '.services.wrapper.ports[0] = "9900:${WRAPPER_IP_PORT}"' docker-compose.dev.yml

# 5. network 변경
new_network="${BSN_CODE}-net"
sed -i "s/our_net/$new_network/g" docker-compose.yml
yq e -i ".networks.\"$new_network\".ipam.config[0].subnet = \"172.10.0.0/16\"" docker-compose.yml

# 6. DOCKER SERVER IP ADDRESS 변경
sed -i '/^\(WRAPPER\|WEB\|SERVING\|PP\)_IP_ADDR=/ s/=.*/='$BSN_CODE'/g' .env

# 7. Docker file user, group 1001:1001 추가
for Dockerfile in $(ls docker/base); do
    `cat docker/base/$Dockerfile | grep -A2 -B2 groupadd | grep useradd > /dev/null`
    if [ $? -ne 1 ]; then
        sed -i'' -r -e "/useradd/a\RUN groupadd -r circleci -g 1001 && useradd -m -u 1001 -r -g circleci -s /sbin/nologin -c \"Circleci user\" circleci && gpasswd -a textscope circleci" docker/base/$Dockerfile
        echo "$Dockerfile add user & group 1001"
    else 
        echo "$Dockerfile is not contain add user & group"
    fi
done    