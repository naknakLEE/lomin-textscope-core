model_config=`cat ../conf/config.yaml | shyaml get-value defaults.2.model`
model_count=`cat ../conf/model/${model_config}.yaml | shyaml get-length resources`
model_count=$((${model_count} - 1))

for index in `seq 0 ${model_count}`
do
    model_path=`cat ../conf/model/${model_config}.yaml | shyaml get-value resources.${index}.model_path`
    path_depth=`echo ${model_path} | tr -cd '/' | wc -m`
    model_path_s3=`echo ${model_path} | cut -d '/' -f 1-${path_depth}`
    echo "[$((${index} + 1))/$((${model_count} + 1))]"
    aws s3 cp ../../${model_path_s3}/ s3://lomin-model-repository/textscope/${model_path_s3}/ --recursive
    echo ""
done