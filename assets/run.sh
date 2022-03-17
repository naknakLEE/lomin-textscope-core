command=$1

docker_command="docker-compose -f docker-compose.yml -f docker-compose.prod.yml"
usage="""
usage: sh run.sh [command] \n\n
run: Run service to foreground\n
run-bg: Run service to background\n
stop: Stop service\n
clean: Cleanup all service-related data\n
"""

if [ -z $1 ]
then
    echo $usage
    exit
fi

if [ $command = "run" ]
then
    $docker_command up
elif [ $command = "run-bg" ]
then
    docker_command up -d
elif [ $command = "stop" ]
then
    $docker_command down
elif [ $command = "clean" ]
    docker stop $(docker ps -aq)
    docker rm -f $(docker ps -aq)
    docker volume prune -f
    docker network prune -f
else
    echo $usage
fi
