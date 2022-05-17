base_path="."

.  ${base_path}/.env

# set build variable
saved_foler_name="${SAVED_FOLDER_NAME}"
build_folder_name="${BUILD_FOLDER_PATH}"
image_repository_list="${IMAGE_REPOSITORY_LIST}"
saved_dir="${base_path}/build/images/${CUSTOMER}"

echo "docker image save start!"
mkdir -p ${saved_dir}
echo "            md5sum                           docker_image_path" > ${saved_dir}/"checksum(md5).txt"

for image in ${image_repository_list}
do
    output_name=$(echo ${image} | awk -F/ '{print $NF}' | tr : _)
    echo ${image} '|' ${output_name}
    docker save ${image} | pigz -6 > ${saved_dir}/${output_name}.tar.gz
    echo `md5sum ${saved_dir}/${output_name}.tar.gz` >> ${saved_dir}/"checksum(md5).txt"
done
echo "docker image save complete!"
