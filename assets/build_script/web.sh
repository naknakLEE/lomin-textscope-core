. /workspace/.env

BUILD_PATH=${WORKSPACE_BUILD_PATH}

# Initialization
mkdir -p ${BUILD_PATH}/web

# web
cd /workspace
python3 -m nuitka --module app --include-package=app --output-dir=${BUILD_PATH}/web
rm -rf ${BUILD_PATH}/web/app.build

# required files
cp /workspace/app/main.py ${BUILD_PATH}/web/.