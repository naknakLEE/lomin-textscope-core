pwd
ls -al

ifconfig

aws configure list
cat ~/.aws/config

aws s3 cp s3://lomin-model-repository/textscope/assets/models/gocr/detection/2/kxm-det-220816-changwoo-02-iter=0054999_f1=97.3104-topk=10000-batch=1.ts app/

cd app && ls -al