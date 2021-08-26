base_path=".."

.  ${base_path}/.env

ENCRYPTED_FOLDER_NAME="encrypted_file"
THALES_LINUXENV="linuxenv"
HVC="TBXBG.hvc"
FEATURE="1"

base_path="."
encrypted_folder_name="${ENCRYPTED_FOLDER_NAME}"
linuxenv="${base_path}/${THALES_LINUXENV}"
hvc="${base_path}/${HVC}" # "./DEMOMA.hvc"
feature="${FEATURE}" # 100

for file in `find $encrypted_folder_name -type f -name "*.so"`
do
    $linuxenv -v:$hvc -f:$feature --dfp $file $file
done