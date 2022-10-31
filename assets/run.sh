command=$1
​
docker_command="docker-compose -f docker-compose.yml -f docker-compose.prod.yml"
usage="""
usage: sh run.sh [command] \n\n
run: Run service to foreground\n
run-bg: Run service to background\n
stop: Stop service\n
clean: Cleanup all service-related data\n
"""
​
if [ -z $1 ]
then
    echo $usage
    exit
fi
​
if [ $command = "run" ]
then
    $docker_command up
elif [ $command = "run-bg" ]
then
    $docker_command up -d
elif [ $command = "stop" ]
then
    $docker_command down
elif [ $command = "clean" ]
then
    docker stop $(docker ps -aq --filter name=textscope*)
    docker rm -f $(docker ps -aq --filter name=textscope*)
    docker volume ls --filter name=grafana_data --filter name=esdata --filter name=minio_data --filter name=prometheus_data --quiet |  xargs --max-args=1 --no-run-if-empty docker volume rm --force
    docker network rm our_net
    echo $usage
fi