set -eux

# set enviroments
sed -i 's/DEVELOP=True/DEVELOP=False/' ./.env
. ./.env
if [ "${CUSTOMER}" = "kbcard" ]; then
    sed -i 's/TIMEOUT_SECOND=30.0/TIMEOUT_SECOND=1200.0/' ./.env
    sed -i 's/MODEL_SERVER_TIMEOUT_SECOND=30/TIMEOUT_SECOND=1200/' ./.env
    sed -i 's/WRAPPER_DATABASE="DOS_TEST"/WRAPPER_DATABASE=${CUSTOMER}/' ./.env
    . ./.env
fi
if [ "${CUSTOMER}" = "kakaobank" ]; then
    sed -i 's/TIMEOUT_SECOND=1200.0/TIMEOUT_SECOND=30.0/' ./.env
    sed -i 's/TIMEOUT_SECOND=1200/MODEL_SERVER_TIMEOUT_SECOND=30/' ./.env
    sed -i 's/WRAPPER_DATABASE=${CUSTOMER}/WRAPPER_DATABASE="DOS_TEST"/' ./.env
    . ./.env
fi

# set build variable
container_list="${CONTAINER_LIST}"
created_folder_name="${CUSTOMER}"
build_folder_name="${BUILD_FOLER}"
inference_server_build_folder_name="inference_server/${BUILD_FOLER}"

# remove previous build folder
rm -rf ./${build_folder_name}/${created_folder_name}
rm -rf ./${inference_server_build_folder_name}/${created_folder_name}

# create compiled file
# docker-compose -f docker-compose.yml -f docker-compose.base.yml build
docker-compose -f docker-compose.build.yml build --parallel
docker-compose -f docker-compose.yml -f docker-compose.build.yml up -d
docker exec -it serving bash -c "sh /workspace/inference_server/assets/envelop_serving_files.sh"

# create build task process folder for lovit
mkdir -p ${build_folder_name}/${created_folder_name}/assets
mkdir -p ${build_folder_name}/${created_folder_name}/lovit/lovit

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

# copy textscope
for container in ${container_list}
do
    echo "Copy ${container} deploy files"
    if [ "${container}" = "pp" ]; then
        mkdir -p ${build_folder_name}/${created_folder_name}/${container}
        app_name="${container}_server"
        docker cp ${container}:/workspace/${app_name}/main.py ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/pp.${SO_EXTENTION} ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/pp.pyi ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/lovit.${SO_EXTENTION} ${build_folder_name}/${created_folder_name}/lovit/ &&
        docker cp ${container}:/workspace/lovit.pyi ${build_folder_name}/${created_folder_name}/lovit/ &&
        docker cp ${container}:/workspace/${app_name}/assets ${build_folder_name}/${created_folder_name}/${container}/assets
    elif [ "${container}" = "web" ]; then
        mkdir -p ${build_folder_name}/${created_folder_name}/${container}
        docker cp ${container}:/workspace/main.py ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/app.${SO_EXTENTION} ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/app.pyi ${build_folder_name}/${created_folder_name}/${container}/
    elif [ "${container}" = "serving" ]; then
        app_name="serving"
        mkdir -p ${inference_server_build_folder_name}/${created_folder_name}/${container}/assets/document_understanding
        mkdir -p ${inference_server_build_folder_name}/${created_folder_name}/lovit
        docker cp ${container}:/root/bentoml/bentos/textscope_model_service ${inference_server_build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/assets/bentoml_configuration.yml ${inference_server_build_folder_name}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/modified_bentoml_file ${inference_server_build_folder_name}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/models/document_understanding/tokenizer ${inference_server_build_folder_name}/${created_folder_name}/${container}/assets/document_understanding/tokenizer &&
        docker cp ${container}:/workspace/lovit.${SO_EXTENTION} ${inference_server_build_folder_name}/${created_folder_name}/lovit/ &&
        docker cp ${container}:/workspace/lovit.pyi ${inference_server_build_folder_name}/${created_folder_name}/lovit/
    else
        echo "Not found!"
    fi
done

docker-compose down

# sh assets/apply-thales.sh"
# docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
