docker-compose -f docker-compose.yml -f docker-compose.build.yml build
docker-compose -f docker-compose.yml -f docker-compose.build.yml up -d

rm -rf encrypted_file

container_list="web pp wrapper serving"
for container in ${container_list}
do 
    mkdir -p encrypted_file/${container}
    echo ${container}
    if [ "${container}" = "wrapper" ]; then
        app_name="kakaobank_${container}"
        docker cp ${container}:/workspace/${app_name}/main.py encrypted_file/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.cpython-36m-x86_64-linux-gnu.so encrypted_file/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.pyi encrypted_file/${container}/
    elif [ "${container}" = "pp" ]; then
        app_name="${container}_server"
        docker cp ${container}:/workspace/${app_name}/main.py encrypted_file/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.cpython-36m-x86_64-linux-gnu.so encrypted_file/${container}/ &&
        docker cp ${container}:/workspace/${app_name}/${app_name}.pyi encrypted_file/${container}/ &&
        docker cp ${container}:/workspace/lovit.cpython-36m-x86_64-linux-gnu.so encrypted_file/ &&
        docker cp ${container}:/workspace/lovit.pyi encrypted_file/
    elif [ "${container}" = "web" ]; then
        docker cp ${container}:/workspace/main.py encrypted_file/ &&
        docker cp ${container}:/workspace/app.cpython-36m-x86_64-linux-gnu.so encrypted_file/ &&
        docker cp ${container}:/workspace/app.pyi encrypted_file/
    elif [ "${container}" = "serving" ]; then
        app_name="inference_server"
        docker cp ${container}:/workspace/${app_name}/ModelService encrypted_file/${container}/ &&
        docker cp ${container}:/usr/local/lib/python3.6/dist-packages/bentoml/frameworks encrypted_file/${container}/
        mv encrypted_file/${container}/ModelService encrypted_file/${container}/CopiedModelService
    else
        echo "not found!"
    fi
done

docker-compose down

# docker-compose -y rm
# docker cp ${container}:/workspace/inference_server/KakaobankModelService/lovit.pyi encrypted_file/${container}/ &&
# docker cp ${container}:/workspace/inference_server/KakaobankModelService/lovit.cpython-36m-x86_64-linux-gnu.so encrypted_file/${container}/ &&