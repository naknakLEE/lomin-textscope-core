base_path=".."

.  ${base_path}/.env

echo "start!"
# remove docker images
image_repository_list="${IMAGE_REPOSITORY_LIST}"
for image in ${image_repository_set}
do
    image_name=$(echo ${image} | awk -F/ '{print $NF}')
    converted_image_name=$(echo ${image_name} | tr : _)
    echo ${converted_image_name}
    docker load -i ${converted_image_name}
done
echo "complete!"
