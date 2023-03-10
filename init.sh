set -eux

# Obtaining the root password
set +x
printf "sudo Password: "
read PASSWORD
set -x

create_log_folder() {
  echo $PASSWORD | sudo -S mkdir -p $MOUNT_LOG_PATH
  echo $PASSWORD | sudo -S chown -R $(id -u $(whoami)):$(id -g $(whoami)) $(dirname "$MOUNT_LOG_PATH")
}

# Init submodule
git submodule update --init --recursive

# Download models
python3 inference_server/assets/cloud_storage/boto3_download_data.py

# Download core assets
python3 assets/cloud_storage/boto3_download_data.py --download_object_name thales

# Download environments
aws s3 cp s3://lomin-model-repository/textscope/.env .env

# Create log folder and change owner
set +x
. ./.env
set -x
create_log_folder

# Build docker containers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel
