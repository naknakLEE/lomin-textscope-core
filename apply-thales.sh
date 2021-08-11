docker-compose -f docker-compose.yml -f docker-compose.build.yml build
docker-compose -f docker-compose.yml -f docker-compose.build.yml up -d

container_list="web pp wrapper serving"
for container in $container_list
do 
    mkdir -p encrypted_file/$container
    docker cp web:/workspace/main.py ./encrypted_file/$container/main.py
    docker cp web:/workspace/app.cpython-36m-x86_64-linux-gnu.so ./encrypted_file/$container/app.cpython-36m-x86_64-linux-gnu.so
    docker cp web:/workspace/app.pyi ./encrypted_file/$container//app.pyi
done

docker-compose down
docker-compose -y rm