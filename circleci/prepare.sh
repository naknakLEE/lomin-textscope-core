#!/bin/bash
set -eux

set +x

BSN_CODE=$1

echo "BSN_CODE is: $BSN_CODE"
# echo "BSN_CODE=$BSN_CODE" | tee .env

PATH="$HOME/.local/bin:$PATH"

########## 1. Submodule Update Start ##########
# ssh-keyscan github.com >> ~/.ssh/known_hosts
# mkdir -p /home/circleci/.config/ssh && cp ~/.ssh/id_rsa ~/.config/ssh/id_rsa

git submodule update --init --recursive
########## 1. Submodule Update End   ##########


########## 2. Download Model File Start ##########
model_config=`cat inference_server/assets/conf/config.yaml | shyaml get-value defaults.2.model`
if test [$model_config='default'];
then
    echo "Change Model Config To ${BSN_CODE}"
    # model_config=${BSN_CODE//-/_}
    model_config=bsn_2211_kbc
    sed -i "s/model: default/model: ${model_config}/" inference_server/assets/conf/config.yaml
fi

model_count=`cat inference_server/assets/conf/model/${model_config}.yaml | shyaml get-length resources`
model_count=$((${model_count} - 1))

aws configure list

for index in `seq 0 ${model_count}`
do
    model_name=`cat inference_server/assets/conf/model/${model_config}.yaml | shyaml get-value resources.${index}.name`
    model_path=`cat inference_server/assets/conf/model/${model_config}.yaml | shyaml get-value resources.${index}.model_path`
    template_path=`cat inference_server/assets/conf/model/${model_config}.yaml | shyaml get-value resources.${index}.template_path False`    
    

    echo "[$((${index} + 1))/$((${model_count} + 1))] ${model_name}"

    if [[ "rotate detection recognition" =~ "${model_name}"* ]]; then
        echo -e "continue ${model_name} for prevent duplication\r\n"
        continue
    fi

    if test -f inference_server/${model_path}; then
        echo -e "Already exist\r\n"
    else
        path_depth=`echo ${model_path} | tr -cd '/' | wc -m`
        model_path_s3=`echo ${model_path} | cut -d '/' -f 1-${path_depth}`
        
        aws s3 cp s3://lomin-model-repository/textscope/${model_path} inference_server/${model_path_s3}/ --recursive
    fi

    if [ ${template_path} != False ];
    then
        cp -r /home/lomin/Templates/${BSN_CODE}/synthcard inference_server/e2e_inference/assets    
    fi
        
done
########## 2. Download Model File End    ##########
set -x