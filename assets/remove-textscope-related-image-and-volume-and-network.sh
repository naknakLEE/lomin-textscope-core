base_path=".."

.  ${base_path}/.env

echo "remove textscope related ... start!"
# remove docker volume
docker volume prune --force

# remove docker network
docker network prune --force

# remove docker images
image_repository_list="${IMAGE_REPOSITORY_LIST}"
for image in ${image_repository_list}
do
    echo ${image}
    docker rmi ${image}
done
echo "remove textscope related ... complete!"
