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
####################################################################vv
# model을 build폴더로 저장하는 로직
rm -rf build/textscope/serving/models
mkdir -p build/textscope/serving/models
bsn_name_before_split=`cat inference_server/assets/conf/config.yaml | grep model`
bsn_name=${bsn_name_before_split##*- model:}
bsn_name=`echo $bsn_name | tr -d ' '`
echo $bsn_name

model_length=`cat inference_server/assets/conf/model/${bsn_name}.yaml | shyaml get-length resources`
model_length=$((model_length - 1))
range=$(seq 0 ${model_length})
for i in $range # 모델 전체 개수 for 돌면서
do
    if cat inference_server/assets/conf/model/${bsn_name}.yaml | shyaml get-value resources.${i}.copy_container; then # copy_container변수명 존재 체크
        is_copy=`cat inference_server/assets/conf/model/${bsn_name}.yaml | shyaml get-value resources.${i}.copy_container`
        if [ "$is_copy" = True ] ; then # copy_container가 true면 build 폴더에 copy
            # copy model
            model_path=`cat inference_server/assets/conf/model/${bsn_name}.yaml | shyaml get-value resources.${i}.model_path`
            build_model_path=${model_path#assets/}
            filename=${build_model_path##*/} # split / get last char
            folder_path=`echo $build_model_path | rev | cut -d '/' -f2- | rev ` # /로 나누고 마지막(파일명) 제외

            mkdir -p build/textscope/serving/${folder_path}
            cp inference_server/${model_path} build/textscope/serving/${build_model_path}

            # copy meta data
            if cat inference_server/assets/conf/model/${bsn_name}.yaml | shyaml get-value resources.${i}.model_metadata; then
                metedata_path=`cat inference_server/assets/conf/model/${bsn_name}.yaml | shyaml get-value resources.${i}.model_metadata`
                build_metadata_path=${metedata_path#assets/}
                metadata_filename=${build_metadata_path##*/} # split / get last char
                metadata_folder_path=`echo $build_metadata_path | rev | cut -d '/' -f2- | rev ` # /로 나누고 마지막(파일명) 제외

                mkdir -p build/textscope/serving/${metadata_folder_path}
                cp inference_server/${metedata_path} build/textscope/serving/${build_metadata_path}
            fi
        fi
    else
        echo "Optional value(copy_container) does not exist. I'll skip that line."
    fi
done

# to inference build folder
mkdir -p build/textscope/serving/models
cp -r build/textscope/serving/models inference_server/build/textscope/serving/models
####################################################################vv
docker-compose down

# sh assets/apply-thales.sh"
# docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
