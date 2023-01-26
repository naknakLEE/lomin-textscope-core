#!/bin/bash
set -eux

set +x

pwd
ls -al
whoami

########## 1. Prepare Start ##########
pip3 install hydra-core python-dotenv alive_progress awscli

ssh-keyscan github.com >> ~/.ssh/known_hosts
mkdir -p /home/circleci/.config/ssh && cp ~/.ssh/id_rsa ~/.config/ssh/id_rsa

git submodule update --init --recursive
########## 1. Prepare End   ##########


########## 2. Download Model File Start ##########
# if [ -z "$BASH_VERSION" ]; then exec bash "$0" "$@"; exit; fi
PATH="$HOME/.local/bin:$PATH"

if pip list | grep shyaml; then
    echo "shyaml installed"
else
    echo "shyaml not installed"
    pip install shyaml
fi

model_config=`cat inference_server/assets/conf/config.yaml | shyaml get-value defaults.2.model`
model_count=`cat inference_server/assets/conf/model/${model_config}.yaml | shyaml get-length resources`
model_count=$((${model_count} - 1))

aws configure list

for index in `seq 0 ${model_count}`
do
    model_name=`cat inference_server/assets/conf/model/${model_config}.yaml | shyaml get-value resources.${index}.name`
    model_path=`cat inference_server/assets/conf/model/${model_config}.yaml | shyaml get-value resources.${index}.model_path`

    echo "[$((${index} + 1))/$((${model_count} + 1))] ${model_name}"

    if [["rotate detection recognition"=~"${model_name}"*]];
    then
        echo -e "continue ${model_name} for prevent duplication\r\n"
        continue
    fi

    if test -f inference_server/${model_path}; then
        echo -e "Already exist\r\n"
    else
        path_depth=`echo ${model_path} | tr -cd '/' | wc -m`
        model_path_s3=`echo ${model_path} | cut -d '/' -f 1-${path_depth}`
        
        # aws s3 cp s3://lomin-model-repository/textscope/${model_path_s3} inference_server/${model_path_s3}/ --recursive
        aws s3 cp s3://lomin-model-repository/textscope/${model_path} inference_server/${model_path_s3}/ --recursive
        echo ""
    fi
done
########## 2. Download Model File End    ##########

########## 3. Docker Build Start    ##########
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel
########## 3. Docker Build End      ##########
set -x