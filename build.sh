set -eux

# set enviroments
sed -i 's/DEVELOP="True"/DEVELOP="False"/' ./.env
. ./.env
if [ "${CUSTOMER}" = "kbcard" ]; then
    sed -i 's/TIMEOUT_SECOND=30.0/TIMEOUT_SECOND=1200.0/' ./.env
    sed -i 's/MODEL_SERVER_TIMEOUT_SECOND=30/TIMEOUT_SECOND=1200/' ./.env
    sed -i 's/WRAPPER_DATABASE="DOS_TEST"/WRAPPER_DATABASE="${CUSTOMER}"/' ./.env
    . ./.env
fi
if [ "${CUSTOMER}" = "kakaobank" ]; then
    sed -i 's/TIMEOUT_SECOND=1200.0/TIMEOUT_SECOND=30.0/' ./.env
    sed -i 's/TIMEOUT_SECOND=1200/MODEL_SERVER_TIMEOUT_SECOND=30/' ./.env
    sed -i 's/WRAPPER_DATABASE="${CUSTOMER}"/WRAPPER_DATABASE="DOS_TEST"/' ./.env
    . ./.env
fi

# set build variable
container_list="${CONTAINER_LIST}"
created_folder_name="${CUSTOMER}-build"
build_folder_name="${BUILD_FOLER}"
inference_server_build_folder_name="${INFERENCE_APP_NAME}/${BUILD_FOLER}"

# remove previous build folder
rm -rf ./${build_folder_name}/${created_folder_name}

# create compiled file
# docker-compose -f docker-compose.yml -f docker-compose.base.yml build
docker-compose -f docker-compose.build.yml build --parallel
docker-compose -f docker-compose.yml -f docker-compose.build.yml up -d
docker exec -it serving bash -c "sh /workspace/inference_server/assets/envelop_serving_files.sh"

# create build task process folder for lovit and wrapper
mkdir -p ${build_folder_name}/${created_folder_name}/wrapper
mkdir -p ${build_folder_name}/${created_folder_name}/assets
mkdir -p ${build_folder_name}/${created_folder_name}/lovit/lovit

# copy wrapper
app_name="${CUSTOMER}_wrapper"
cp -r ./${app_name} ${build_folder_name}/${created_folder_name}/wrapper/
cp -r ./${app_name} ${build_folder_name}/${created_folder_name}/assets/
if [ "${CUSTOMER}" = "kbcard" ]; then
    rm -rf ${build_folder_name}/${created_folder_name}/wrapper/${app_name}/assets
fi

# copy config
config_file_list="${CONFIG_FILE_LIST}"
for file in ${config_file_list}
do
    echo ${file}
    cp -r ./${file} ${build_folder_name}/${created_folder_name}/assets/
done

# copy textscope
for container in ${container_list}
do
    echo ${container}
    mkdir -p ${build_folder_name}/${created_folder_name}/${container}
    if [ "${container}" = "pp" ]; then
        app_name="${container}_server"
        docker cp ${container}:/workspace/${app_name}/main.py ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.${SO_EXTENTION} ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.pyi ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/lovit.${SO_EXTENTION} ${build_folder_name}/${created_folder_name}/lovit/ &&
        docker cp ${container}:/workspace/lovit.pyi ${build_folder_name}/${created_folder_name}/lovit/ &&
        docker cp ${container}:/workspace/${app_name}/assets ${build_folder_name}/${created_folder_name}/${container}/assets
    elif [ "${container}" = "web" ]; then
        docker cp ${container}:/workspace/main.py ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/app.${SO_EXTENTION} ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/app.pyi ${build_folder_name}/${created_folder_name}/${container}/
    elif [ "${container}" = "serving" ]; then
        app_name="inference_server"
        mkdir -p ${inference_server_build_folder_name}/${created_folder_name}/${container}/assets/document_understanding
        mkdir -p ${inference_server_build_folder_name}/${created_folder_name}/lovit
        docker cp ${container}:/root/bentoml/bentos/textscope_model_service ${inference_server_build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/assets/bentoml_configuration.yml ${inference_server_build_folder_name}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/modified_bentoml_file ${inference_server_build_folder_name}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/models/document_understanding/tokenizer ${inference_server_build_folder_name}/${created_folder_name}/${container}/assets/document_understanding/tokenizer &&
        docker cp ${container}:/workspace/lovit.${SO_EXTENTION} ${inference_server_build_folder_name}/${created_folder_name}/lovit/ &&
        docker cp ${container}:/workspace/lovit.pyi ${inference_server_build_folder_name}/${created_folder_name}/lovit/
    else
        echo "not found!"
    fi
done

mkdir -p ${build_folder_name}/${created_folder_name}/workspace
cp -r ${build_folder_name}/${created_folder_name}/assets ${build_folder_name}/${created_folder_name}/workspace/
cp -r ${build_folder_name}/${created_folder_name}/wrapper/ ${build_folder_name}/${created_folder_name}/workspace/
cp ${build_folder_name}/${created_folder_name}/assets/.env ${build_folder_name}/${created_folder_name}/.env
mv ${build_folder_name}/${created_folder_name}/assets/run.sh ${build_folder_name}/${created_folder_name}/run.sh
mv ${build_folder_name}/${created_folder_name}/assets/deploy-setup.sh ${build_folder_name}/${created_folder_name}/deploy-setup.sh

docker-compose down

# ssh sentinel@127.0.0.1 -p2222 "sudo sh /media/sf_Textscope/assets/apply-thales.sh"
# docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
