#!/bin/bash

BSN_CODE=$1

# .env 파일에 개행 문자 삭제(context에 base64 encoding된 값을 decoding하는 방식이라 그런지 개행 문자가 linux와 달라서 이슈 생김)
sed -i 's/\r$//' .env
chmod 770 ./ && chmod 654 assets/build_script/*
sh build.sh
# docker-compose.build.yml의 container name 변경
cat docker-compose.build.yml | shyaml keys services | { 
    while read service; do                     
        m_c_name="${BSN_CODE}-${service}"
        yq e -i ".services.\"$service\".container_name = \"$m_c_name\"" docker-compose.build.yml
        echo "Success fix ${service} container name to $m_c_name"                
    done; 
}|| true


sh build.sh