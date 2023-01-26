pwd

########## 1. Delete Docker Container & Volume and Network Start ##########
docker-compose -f docker-compose.yml -f docker-compose.dev.yml config | 
shyaml keys services | { 
    while read services; 
    do 
    docker stop $services; 
    docker rm $services; 
    done; 
}|| true


docker-compose -f docker-compose.yml -f docker-compose.dev.yml config | 
shyaml keys networks | { 
    while read network; 
    do 
    docker network inspect $network | 
    grep Name | 
    grep -v $network | 
    cut -d '"' -f4 | { 
        while read service; 
        do 
        docker stop  $service; 
        docker rm $service; 
        done; 
    }; 
    if docker network rm $network ; then
        echo "$network network rm successful"
    else
        echo "$network There is no container connected to the docker network"
    fi
    done; 
}|| true

docker volume rm $(docker volume ls --filter name=${PWD##*/}_ --format "{{.Name}}") || true
########## 1. Delete Docker Container & Volume and Network End   ##########


########## 2. Docker Build Start    ##########
{
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel
} || {
    systemctl restart docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel
}
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
########## 2. Docker Build End      ##########