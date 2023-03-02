#!/bin/bash
set -eux

set +x

BSN_CODE=$1

echo "BSN_CODE is: $BSN_CODE"
# echo "BSN_CODE=$BSN_CODE" | tee .env

PATH="$HOME/.local/bin:$PATH"

########## 1. Download Model File Start ##########
model_config=`cat inference_server/assets/conf/config.yaml | shyaml get-value defaults.2.model`
if [ $model_config = 'default' ]; then
    echo "Change Model Config To ${BSN_CODE}"
    model_config=`echo ${BSN_CODE:0:12} | sed 's/-/_/g'`
    if [ ! -e inference_server/assets/conf/model/${model_config}.yaml ]; then
        model_config=`echo ${BSN_CODE:0:13} | sed 's/-/_/g'`
    fi
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
    tokenizer_path=`cat inference_server/assets/conf/model/${model_config}.yaml | shyaml get-value resources.${index}.tokenizer_path False`    
    

    echo "[$((${index} + 1))/$((${model_count} + 1))] ${model_name}"

    path_depth=`echo ${model_path} | tr -cd '/' | wc -m`
    model_path_s3=`echo ${model_path} | cut -d '/' -f 1-${path_depth}`

    if test -f inference_server/${model_path}; then
        echo -e "Already exist\r\n"
    else
        path_depth=`echo ${model_path} | tr -cd '/' | wc -m`
        model_path_s3=`echo ${model_path} | cut -d '/' -f 1-${path_depth}`
        
        aws s3 cp s3://lomin-model-repository/textscope/${model_path_s3} inference_server/${model_path_s3}/ --recursive
    fi
    
    if [ $template_path != False ];
    then
        cp -r ~/Circleci/assets/synthcard/$BSN_CODE inference_server/e2e_inference/assets    
    fi

    if [ $tokenizer_path != False ];
    then
        tokenizer_depth=`echo ${tokenizer_path} | tr -cd '/' | wc -m`
        tokenizer_dir=`echo ${tokenizer_path} | cut -d '/' -f 1-${tokenizer_depth}`
        cp -r ~/Circleci/$tokenizer_path $tokenizer_dir 
    fi    
        
done
########## 1. Download Model File End    ##########
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel wrapper web serving pp

# error=`docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel wrapper web serving pp 2>&1`
# if [ $? -ne 0 ]; then
#     echo $error
#     docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel wrapper web serving pp
# fi    
set -x