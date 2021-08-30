# set enviroments
. ./.env

# set build variable
base_path="${BASE_BUILD_PATH}"
container_list="${CONTAINER_LIST}"
created_folder_name="${CUSTOMER}-build"
build_folder_name="${BUILD_FOLDER_PATH}"

# remove previous build folder
rm -rf ${base_path}/${created_folder_name}
rm -rf ./${build_folder_name}/${created_folder_name}

# create compiled file
# docker-compose -f docker-compose.yml -f docker-compose.base.yml build
docker-compose -f docker-compose.yml -f docker-compose.build.yml build
docker-compose -f docker-compose.yml -f docker-compose.build.yml up -d

# create build task process folder for lovit and wrapper
mkdir -p ${base_path}/${created_folder_name}/wrapper
mkdir -p ${base_path}/${created_folder_name}/lovit

# copy wrapper
app_name="${CUSTOMER}_wrapper"
cp -r ./${app_name} ${base_path}/${created_folder_name}/wrapper/
rm -rf ${base_path}/${created_folder_name}/wrapper/${app_name}/${app_name}/tests
rm -rf ${base_path}/${created_folder_name}/wrapper/${app_name}/assets

# copy config
config_file_list="${CONFIG_FILE_LIST}"
for file in ${config_file_list}
do 
    echo ${file}
    cp ./${file} ${base_path}/${created_folder_name}/wrapper/
done

# copy textscope
for container in ${container_list}
do 
    echo ${container}
    mkdir -p ${base_path}/${created_folder_name}/${container}
    if [ "${container}" = "pp" ]; then
        app_name="${container}_server"
        docker cp ${container}:/workspace/${app_name}/main.py ${base_path}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.cpython-36m-x86_64-linux-gnu.so ${base_path}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.pyi ${base_path}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/lovit.cpython-36m-x86_64-linux-gnu.so ${base_path}/${created_folder_name}/lovit/ &&
        docker cp ${container}:/workspace/lovit.pyi ${base_path}/${created_folder_name}/lovit/
    elif [ "${container}" = "web" ]; then
        docker cp ${container}:/workspace/main.py ${base_path}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/app.cpython-36m-x86_64-linux-gnu.so ${base_path}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/app.pyi ${base_path}/${created_folder_name}/${container}/
    elif [ "${container}" = "serving" ]; then
        app_name="inference_server"
        mkdir -p ${base_path}/${created_folder_name}/${container}/assets
        docker cp ${container}:/workspace/${app_name}/ModelService ${base_path}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/assets/textscope_${CUSTOMER}.json ${base_path}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/bentoml_configuration.yml ${base_path}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/gulim.ttc ${base_path}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/modified_bentoml_file ${base_path}/${created_folder_name}/${container}/assets/ &&
        docker cp ${container}:/workspace/${app_name}/assets/bentoml-for-health-check ${base_path}/${created_folder_name}/${container}/assets/        
        docker cp ${container}:/usr/local/lib/python3.6/dist-packages/bentoml/frameworks ${base_path}/${created_folder_name}/${container}/
        mv ${base_path}/${created_folder_name}/${container}/ModelService ${base_path}/${created_folder_name}/${container}/CopiedModelService
    else
        echo "not found!"
    fi
done

# copy from save folder to textscope
rm -rf ./${build_folder_name}
cp -r ${base_path}/${created_folder_name} ./${build_folder_name}

docker-compose down

# test process
# docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
# docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
# test_textscope.py