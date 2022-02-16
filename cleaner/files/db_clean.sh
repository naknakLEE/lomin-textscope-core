echo "-------------------------------------------------------------------"
imageResult=$(PGPASSWORD=1q2w3e4r psql textscope -U lomin -h master_pgpool -c "delete from image where create_datetime < now() AT TIME ZONE 'Asia/Seoul' - interval '180 day';")
taskResult=$(PGPASSWORD=1q2w3e4r psql textscope -U lomin -h master_pgpool -c "delete from task where create_datetime < now() AT TIME ZONE 'Asia/Seoul' - interval '180 day';")
inferenceResult=$(PGPASSWORD=1q2w3e4r psql textscope -U lomin -h master_pgpool -c "delete from inference where create_datetime < now() AT TIME ZONE 'Asia/Seoul' - interval '180 day';")

nowDate=`date`

echo $nowDate": remove old image row "$imageResult
echo $nowDate": remove old task row "$taskResult
echo $nowDate": remove old inference row "$inferenceResult
echo "-------------------------------------------------------------------"
