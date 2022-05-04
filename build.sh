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
docker exec -it serving bash -c "sh /workspace/inference_server/assets/build_script/serving.sh"
docker exec -it web bash -c "sh /workspace/assets/build_script/web.sh"
docker exec -it pp bash -c "sh /workspace/assets/build_script/pp.sh"

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

docker-compose down

# sh assets/apply-thales.sh"
# docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel
