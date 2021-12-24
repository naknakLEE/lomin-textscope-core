set -eux

. /workspace/.env

export ARTIFACT_NAME_LIST=$ARTIFACT_NAME_LIST
export CUSTOMER=$CUSTOMER

APP_NAME=${INFERENCE_SERVER_APP_NAME}

cd /workspace/${APP_NAME}
rm -rf /workspace/${APP_NAME}/ModelService
python3 ${APP_NAME}/generate_${CUSTOMER}_model_service.py 

cd /usr/local/lib/python${PYTHON_VERSION}/dist-packages/bentoml/frameworks/
cp /workspace/${APP_NAME}/assets/modified_bentoml_file/pytorch.py /usr/local/lib/python${PYTHON_VERSION}/dist-packages/bentoml/frameworks/pytorch.py
python3 -m nuitka --module pytorch.py
rm -r pytorch.py pytorch.build __pycache__
cp /workspace/${APP_NAME}/assets/modified_bentoml_file/${CUSTOMER}_loader.py /usr/local/lib/python${PYTHON_VERSION}/dist-packages/bentoml/saved_bundle/loader.py
cp /workspace/${APP_NAME}/assets/modified_bentoml_file/pip_pkg.py /usr/local/lib/python${PYTHON_VERSION}/dist-packages/bentoml/saved_bundle/pip_pkg.py

cp /workspace/${APP_NAME}/assets/modified_bentoml_file/onnx.py /usr/local/lib/python${PYTHON_VERSION}/dist-packages/bentoml/frameworks/onnx.py
python3 -m nuitka --module onnx.py
rm -r onnx.py onnx.build

cd ${BUNDLE_PATH}
cp -r /workspace/${APP_NAME}/lovit .
python3 /workspace/${APP_NAME}/${APP_NAME}/encrytion.py
python3 -m nuitka --module ${APP_NAME} --include-package=${APP_NAME}

python3 -m nuitka --module lovit --include-package=lovit
    find lovit/* -maxdepth 0 -name 'resources' -prune -o -exec rm -rf '{}' ';'

rm -r /workspace/bentoml /workspace/assets /workspace/Nuitka
rm -r /workspace/${APP_NAME}/${APP_NAME} /workspace/${APP_NAME}/lovit /workspace/*.txt
rm -r ${BUNDLE_PATH}/${APP_NAME} ${BUNDLE_PATH}/*.build
rm -rf /var/lib/apt/lists/*
