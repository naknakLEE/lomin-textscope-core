directory="encrypted_file"
linuxenv="./linuxenv"
hvc="./TBXBG.hvc" # "./DEMOMA.hvc"
feature="1" # 100

for file in `find $directory -type f -name "*.so"`
do
    $linuxenv -v:$hvc -f:$feature --dfp $file $file
done