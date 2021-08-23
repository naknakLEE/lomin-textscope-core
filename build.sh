# source .env

base_path="others/sentinel"
container_list="web pp wrapper serving"
# customer="${CUSTOMER}"
customer="kakaobank"
created_folder_name="${customer}-build"
build_folder_name="build-folder"

rm -rf ${base_path}/${created_folder_name}

docker-compose -f docker-compose.yml -f docker-compose.build.yml build
docker-compose -f docker-compose.yml -f docker-compose.build.yml up -d

mkdir -p ${base_path}/${created_folder_name}/lovit
for container in ${container_list}
do 
    mkdir -p ${base_path}/${created_folder_name}/${container}
    echo ${container}
    if [ "${container}" = "wrapper" ]; then
        app_name="${customer}_${container}"
        cp -r ./${app_name} ${base_path}/${created_folder_name}/${container}/
        cp ./.env ${base_path}/${created_folder_name}/${container}/
        cp ./docker-compose.yml ${base_path}/${created_folder_name}/${container}/
        cp ./docker-compose.prod.yml ${base_path}/${created_folder_name}/${container}/
        # docker cp ${container}:/workspace/${app_name}/main.py ${base_path}/${created_folder_name}/${container}/ &&
        # docker cp ${container}:/workspace/${app_name}/${app_name}.cpython-36m-x86_64-linux-gnu.so ${base_path}/${created_folder_name}/${container}/ &&
        # docker cp ${container}:/workspace/${app_name}/${app_name}.pyi ${base_path}/${created_folder_name}/${container}/
    elif [ "${container}" = "pp" ]; then
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
        docker cp ${container}:/workspace/${app_name}/ModelService ${base_path}/${created_folder_name}/${container}/ &&
        docker cp ${container}:/usr/local/lib/python3.6/dist-packages/bentoml/frameworks ${base_path}/${created_folder_name}/${container}/
        mv ${base_path}/${created_folder_name}/${container}/ModelService ${base_path}/${created_folder_name}/${container}/CopiedModelService
    else
        echo "not found!"
    fi
done

mkdir -p ${build_folder_name}
cp -r ${base_path}/${created_folder_name} ./${build_folder_name}/

docker-compose down
