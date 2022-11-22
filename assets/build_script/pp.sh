. /workspace/.env

BUILD_PATH=${WORKSPACE_BUILD_PATH}

# Initialization
mkdir -p ${BUILD_PATH}/lovit/lovit
mkdir -p ${BUILD_PATH}/pp

# pp nuitka
cd /workspace/pp_server
python3 -m nuitka --module pp --include-package=pp --output-dir=${BUILD_PATH}/pp
rm -rf ${BUILD_PATH}/pp/pp.build

# lovit nuitka
cd /workspace/pp_server/lovit
python3 -m nuitka --module lovit --include-package=lovit --output-dir=${BUILD_PATH}/lovit
rm -rf ${BUILD_PATH}/lovit/lovit.build

# required files
cp /workspace/pp_server/pp/main.py ${BUILD_PATH}/pp/.
cp -r /workspace/pp_server/assets ${BUILD_PATH}/pp/.