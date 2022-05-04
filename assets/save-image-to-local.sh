base_path="."

.  ${base_path}/.env

# set build variable
saved_foler_name="${SAVED_FOLDER_NAME}"
build_folder_name="${BUILD_FOLDER_PATH}"
image_repository_list="${IMAGE_REPOSITORY_LIST}"
saved_dir="${base_path}/build/images/${CUSTOMER}"

echo "docker image download start!"
mkdir -p ${saved_dir}

echo "start docker image download process!"
for image in ${image_repository_list}
do
    output_name=$(echo ${image} | awk -F/ '{print $NF}' | tr : _)
    echo ${image} '|' ${output_name}
    # docker save -o ${saved_dir}/${output_name}.tar ${image}# 일반 
    docker save ${image} | pigz -6 > ${saved_dir}/${output_name}.tar.gz # 압축

done
echo "docker image download complete!"
