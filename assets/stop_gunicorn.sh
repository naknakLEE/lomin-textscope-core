CONTAINER_LIST="wrapper web pp serving serving_replica"

for container in ${CONTAINER_LIST}
do
    GP=$(docker exec -it ${container} ps ax | grep -e gunicorn -e serve-g | awk '{print $1}' | head -n 1)
    if [ "${#GP}" -gt 0 ]; then
        docker exec -it ${container} kill -TERM $GP
        echo "$container $GP process terminated"
    fi
done
