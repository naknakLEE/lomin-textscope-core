directory="encrypted_file"
linuxenv="./linuxenv"
hvc="./DEMOMA.hvc"
feature="100"

find $directory -type f -name "*.so"

-f:100 --dfp mock-up.bin lo_mock-up.bin
for file in `find $directory -type f -name "*.so"`
do
    $linuxenv -v:$hvc -f:$feature --dfp $file $file
done