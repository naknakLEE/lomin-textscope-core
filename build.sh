#!/bin/bash

set -eux

# set enviroments
sed 's/DEVELOP=True/DEVELOP=False/' ./.env | tee .env.prod
. ./.env.prod
if [ "${CUSTOMER}" = "kbcard" ]; then
    sed 's/TIMEOUT_SECOND=30.0/TIMEOUT_SECOND=1200.0/' ./.env.prod | tee .env.prod
    sed 's/MODEL_SERVER_TIMEOUT_SECOND=30/TIMEOUT_SECOND=1200/' ./.env.prod | tee .env.prod
    sed 's/WRAPPER_DATABASE="DOS_TEST"/WRAPPER_DATABASE=${CUSTOMER}/' ./.env.prod | tee .env.prod
    . ./.env.prod
fi
if [ "${CUSTOMER}" = "kakaobank" ]; then
    sed 's/TIMEOUT_SECOND=1200.0/TIMEOUT_SECOND=30.0/' ./.env.prod | tee .env.prod
    sed 's/TIMEOUT_SECOND=1200/MODEL_SERVER_TIMEOUT_SECOND=30/' ./.env.prod | tee .env.prod
    sed 's/WRAPPER_DATABASE=${CUSTOMER}/WRAPPER_DATABASE="DOS_TEST"/' ./.env.prod | tee .env.prod
    . ./.env.prod
fi

# set build variable
export_files_container_list="${CONTAINER_LIST}"
created_folder_name="${CUSTOMER}"
build_folder_name="${BUILD_FOLER}"
inference_server_build_folder_name="inference_server/${BUILD_FOLER}"

# remove previous build folder
rm -rf ./${build_folder_name}/${created_folder_name}
rm -rf ./${inference_server_build_folder_name}/${created_folder_name}

# create compiled file
docker-compose -f docker-compose.build.yml build --parallel
docker-compose -f docker-compose.build.yml up -d
docker exec -it textscope-serving bash -c "sh /workspace/inference_server/assets/build_script/serving.sh"
docker exec -it textscope-web bash -c "sh /workspace/assets/build_script/web.sh"
docker exec -it textscope-pp bash -c "sh /workspace/assets/build_script/pp.sh"

# copy wrapper
app_name="${CUSTOMER}_wrapper"
cp -r ./${app_name} ${build_folder_name}/${created_folder_name}/assets/
cp -r ./${app_name}/wrapper ${build_folder_name}/${created_folder_name}/wrapper

# copy config
config_file_list="${CONFIG_FILE_LIST}"
for file in ${config_file_list}
do
    echo "Copy config files, ${file}"
    cp -r ./${file} ${build_folder_name}/${created_folder_name}/assets/
done
for file in ${MKDIR_FOLDER_LIST}
do
    echo "Create folder, ${file}"
    mkdir -p ${build_folder_name}/${created_folder_name}/assets/${file}
done

# copy build_so file
cp -r ./assets/build_so/* ${build_folder_name}/${created_folder_name}

####################################################################vv
# ./inference_server/assets/models 폴더의 enc 모델 파일을 ./build/textscope/serving/models 폴더로 저장하는 로직
rm -rf build/textscope/serving/models
mkdir -p build/textscope/serving/models

bsn_name=`cat ./inference_server/assets/conf/config.yaml | shyaml get-value defaults.2.model`
model_config="./inference_server/assets/conf/model/${bsn_name}.yaml"
model_count=`cat ${model_config} | shyaml get-length resources`
model_count=$((${model_count} - 1))

for index in `seq 0 ${model_count}`
do
    model_path="./inference_server/"`cat ${model_config} | shyaml get-value resources.${index}.model_path`
    model_path_length=`echo ${model_path} | tr -cd '/' | wc -m`
    model_parent_path=`echo ${model_path} | cut -d '/' -f 1-${model_path_length}`

    # copy_container가 없거나 False인 경우 모델 복사 안함
    copy_container=`cat ${model_config} | shyaml get-value resources.${index}.copy_container False`
    if [ ${copy_container} != True ];
    then
        echo "Not Copied: ${model_parent_path}"
        echo "Optional value(copy_container) does not exist. I'll skip that line."
        continue
    fi

    # 일단 전부(비암호화 모델, 암호화 모델) 복사 ./inference_server/assets/models/ -> ./build/textscope/serving/models/
    build_model_path="./build/textscope/serving/"`echo ${model_parent_path} | cut -d '/' -f 4-`
    build_model_path_cp=`echo ${build_model_path} | tr -cd '/' | wc -m`
    build_model_path_cp=`echo ${build_model_path} | cut -d '/' -f 1-${build_model_path_cp}`

    mkdir -p ${build_model_path}
    cp -r ${model_parent_path} ${build_model_path_cp}
    echo "Copied: ${model_parent_path} -> ${build_model_path}"


    # ./build/textscope/serving/models/에 있는 비암호화 모델 삭제
    model_path_length=`echo ${model_path} | tr -cd '/' | wc -m`
    model_filename=`echo ${model_path} | cut -d '/' -f $((${model_path_length} + 1))`

    rm ${build_model_path}/${model_filename}
done

# ./inference_server/assets/models/에 있는 암호화된 모델 삭제
find ./inference_server/assets/models/ -name "enc_*" -delete

# to inference build folder
mkdir -p build/textscope/serving/models
cp -r build/textscope/serving/models inference_server/build/textscope/serving/

# copy ./inference_server/build/textscope/serving -> ./build/textscope/serving
cp -r ./inference_server/build/textscope/serving ./build/textscope/

####################################################################vv

docker-compose down

# sh assets/apply-thales.sh"
# docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
