directory="encrypted_file"
linuxenv="./linuxenv"
# hvc="./DEMOMA.hvc"
# feature="100"
hvc="./TBXBG.hvc"
feature="1"

for file in `find $directory -type f -name "*.so"`
do
    $linuxenv -v:$hvc -f:$feature --dfp $file $file
done