SCRIPT_BASE_PATH="."
.  ${SCRIPT_BASE_PATH}/.env

THALES_LINUXENV="linuxenv"
HVC="TBXBG.hvc"
FEATURE="1"
THALES_BASE_PATH="${SCRIPT_BASE_PATH}/assets/thales"
INFERENCE_SERVER_APP_NAME="inference_server"

linuxenv="${THALES_BASE_PATH}/${THALES_LINUXENV}"
hvc="${THALES_BASE_PATH}/${HVC}" # "./DEMOMA.hvc"
feature="${FEATURE}" # 100


core_encrypt_folder="${SCRIPT_BASE_PATH}/${BUILD_FOLDER_PATH}/${CUSTOMER}"
for file in `find $core_encrypt_folder -type f -name "*.so"`
do
    # $linuxenv -v:$hvc -f:$feature --dfp $file $file
    echo
    curl -X 'POST' \
    'http://10.1.1.110:1948/upload-so' \
    -H 'accept: application/json' \
    -H 'Content-Type: multipart/form-data' \
    -F 'file=@'${file}';type=application/x-sharedlib' \
    --output $file
done
serving_encrypt_folder="${SCRIPT_BASE_PATH}/${INFERENCE_SERVER_APP_NAME}/${BUILD_FOLDER_PATH}/${CUSTOMER}"
for file in `find $serving_encrypt_folder -type f -name "*.so"`
do
    # $linuxenv -v:$hvc -f:$feature --dfp $file $file
    echo
    curl -X 'POST' \
    'http://10.1.1.110:1948/upload-so' \
    -H 'accept: application/json' \
    -H 'Content-Type: multipart/form-data' \
    -F 'file=@'${file}';type=application/x-sharedlib' \
    --output $file
done
rm -rf "${core_encrypt_folder}/serving"
cp -r "${serving_encrypt_folder}/serving" "${core_encrypt_folder}/serving"

rm -rf "${core_encrypt_folder}/serving/lovit"
cp -r "${serving_encrypt_folder}/serving/lovit" "${core_encrypt_folder}/serving/lovit"
