current_time_zone=$(date +%Z)

while true
do
    if [ "$current_time_zone" = "KST" ]
    then
        if [ $(date +%H) = "04" ]
        then
            echo wrapper container restart
            docker restart wrapper
            sleep 1d
        else
            sleep 1h
        fi
    elif [ "$current_time_zone" = "UTC" ]
    then
        if [ $(date +%H) = "19" ]
        then
            echo wrapper container restart
            docker restart wrapper
            sleep 1d
        else
            sleep 1h
        fi
    fi    
done        