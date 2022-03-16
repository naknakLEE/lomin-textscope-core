if [ -z "$@" ]
    then
        exit "no args"
fi


cd $@
requirements_file=$(find . -type f -name "pyproject.toml")

echo "dependency file found \"$(readlink -f $requirements_file)\""

poetry check

echo "end"
