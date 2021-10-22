set -eux

# set enviroments
sed -i 's/DEVELOP="True"/DEVELOP="False"/' ./.env
. ./.env
if [ "${CUSTOMER}" = "kbcard" ]; then
    sed -i 's/TIMEOUT_SECOND=30.0/TIMEOUT_SECOND=1200.0/' ./.env
    sed -i 's/MODEL_SERVER_TIMEOUT_SECOND=30/TIMEOUT_SECOND=1200/' ./.env
    sed -i 's/WRAPPER_DATABASE_NAME="${CUSTOMER}"/WRAPPER_DATABASE_NAME="DOS_TEST"/' ./.env
    . ./.env
fi

# set build variable
container_list="${CONTAINER_LIST}"
created_folder_name="${CUSTOMER}-build"
build_folder_name="${BUILD_FOLER}"

# remove previous build folder
rm -rf ./${build_folder_name}/${created_folder_name}

# create compiled file
# docker-compose -f docker-compose.yml -f docker-compose.base.yml build
docker-compose -f docker-compose.build.yml build --parallel
docker-compose -f docker-compose.yml -f docker-compose.build.yml up -d
docker exec -it serving bash -c "sh /workspace/assets/envelop_serving_files.sh"

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
        docker cp ${container}:/workspace/${app_name}/${app_name}.cpython-36m-x86_64-linux-gnu.so ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.pyi ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/lovit.cpython-36m-x86_64-linux-gnu.so ${build_folder_name}/${created_folder_name}/lovit/ &&
        docker cp ${container}:/workspace/lovit.pyi ${build_folder_name}/${created_folder_name}/lovit/
        docker cp ${container}:/workspace/lovit/resources ${build_folder_name}/${created_folder_name}/lovit/lovit/
    elif [ "${container}" = "web" ]; then
        docker cp ${container}:/workspace/main.py ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/app.cpython-36m-x86_64-linux-gnu.so ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/app.pyi ${build_folder_name}/${created_folder_name}/${container}/
    elif [ "${container}" = "serving" ]; then
        app_name="inference_server"
        mkdir -p ${build_folder_name}/${created_folder_name}/${container}/assets
        docker cp ${container}:/workspace/${app_name}/ModelService ${build_folder_name}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/assets/textscope_${CUSTOMER}.json ${build_folder_name}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/bentoml_configuration.yml ${build_folder_name}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/gulim.ttc ${build_folder_name}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/modified_bentoml_file ${build_folder_name}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/bentoml-for-health-check ${build_folder_name}/${created_folder_name}/${container}/assets/        
        docker cp ${container}:/usr/local/lib/python3.6/dist-packages/bentoml/frameworks ${build_folder_name}/${created_folder_name}/${container}/
        mv ${build_folder_name}/${created_folder_name}/${container}/ModelService ${build_folder_name}/${created_folder_name}/${container}/CopiedModelService
    else
        echo "not found!"
    fi
done

mkdir -p ${build_folder_name}/${created_folder_name}/workspace
cp -r ${build_folder_name}/${created_folder_name}/assets ${build_folder_name}/${created_folder_name}/workspace/
cp -r ${build_folder_name}/${created_folder_name}/wrapper/ ${build_folder_name}/${created_folder_name}/workspace/

docker-compose down
