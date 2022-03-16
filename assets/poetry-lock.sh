if [ -z "$@" ]
    then
        exit "no args"
fi


cd $@
requirements_file=$(find . -type f -name "poetry.lock")

echo "lock file found \"$(readlink -f $requirements_file)\""

poetry lock --no-update

echo "end"
