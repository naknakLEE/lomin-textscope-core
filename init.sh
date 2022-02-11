set -eux

# Init submodule
git submodule update --init --recursive

# Download models
python3 inference_server/assets/cloud_storage/boto3_download_data.py

# Download environments
aws s3 cp s3://lomin-model-repository/textscope/.env .env

# Build docker containers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel

# Up docker-compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up