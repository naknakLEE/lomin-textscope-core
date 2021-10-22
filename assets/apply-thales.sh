SCRIPT_BASE_PATH=".."
.  ${SCRIPT_BASE_PATH}/.env

THALES_LINUXENV="linuxenv"
HVC="TBXBG.hvc"
FEATURE="1"
THALES_BASE_PATH="./thales"

linuxenv="${THALES_BASE_PATH}/${THALES_LINUXENV}"
hvc="${THALES_BASE_PATH}/${HVC}" # "./DEMOMA.hvc"
feature="${FEATURE}" # 100

encrypt_folder="${SCRIPT_BASE_PATH}/${BUILD_FOLDER_PATH}/${CUSTOMER}-build"
# cp -r "${encrypt_folder}" "${encrypt_folder}_copy"

for file in `find $encrypt_folder -type f -name "*.so"`
do
    $linuxenv -v:$hvc -f:$feature --dfp $file $file
done