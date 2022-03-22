image_dir=$1

if [ -z $image_dir ]
then
    echo "usage: sh deploy-setup.sh /docker/image/path"
    exit
fi

# load docker image
if [ -d $image_dir ]
then
  load_image_list=$(ls "$1")
  for image in ${load_image_list}
  do
    image_name=$(echo ${image} | awk -F/ '{print $NF}')
    converted_image_name=$(echo ${image_name} | tr : _)
    echo "loading ${image}"
    image_path="$image_dir/$converted_image_name"
    docker load -i ${image_path}
  done
  echo "done!"
else
  echo "$image_dir is not exist. Check path"
fi
