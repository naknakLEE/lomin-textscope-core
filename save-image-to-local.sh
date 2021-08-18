image_repository_set="docker.lomin.ai/ts-web:0.0.1 docker.lomin.ai/ts-gpu-serving:0.0.1 docker.lomin.ai/ts-pp:0.0.1 docker.lomin.ai/ts-wrapper:0.0.1 nginx:latest nginx/nginx-prometheus-exporter:0.9.0 nvcr.io/nvidia/k8s/dcgm-exporter:2.0.13-2.1.2-ubuntu18.04 prom/node-exporter prom/prometheus grafana/grafana prom/mysqld-exporter mysql:8.0.25"
build_folder_name="build-folder"
saved_foler_name="saved-docker-images"
customer="kakaobank"
saved_dir="./${build_folder_name}/${saved_foler_name}/${customer}"

mkdir -p saved_dir
echo "start docker image download process!"
for image in ${image_repository_set}
do
    output_name=$(echo ${image} | awk -F/ '{print $NF}')
    echo ${image} 
    echo ${output_name}
    docker save -o ${saved_dir}/${output_name} ${image}
done
echo "docker image download complete!"