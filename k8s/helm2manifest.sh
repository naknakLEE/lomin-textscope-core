# USAGE sh helm2manifest.sh {develop or production}
if [ $# -eq 0 ] ; then
    echo "Warning: no arguments"
    exit 0
fi
dev_prod_mode=$1
k8s_root_path="values"
manifest_save_path="manifest"
template_folder="textscope"


helm template -f ${k8s_root_path}/${dev_prod_mode}/minio.yaml minio-textscope bitnami/minio --output-dir ${manifest_save_path}/${dev_prod_mode}/minio
helm template -f ${k8s_root_path}/${dev_prod_mode}/postgresql.yaml postgresql-textscope bitnami/postgresql --output-dir  ${manifest_save_path}/${dev_prod_mode}/postgresql

helm template -f ${k8s_root_path}/${dev_prod_mode}/wrapper.yaml wrapper ${template_folder} --output-dir  ${manifest_save_path}/${dev_prod_mode}/wrapper
helm template -f ${k8s_root_path}/${dev_prod_mode}/serving.yaml serving ${template_folder} --output-dir  ${manifest_save_path}/${dev_prod_mode}/serving
helm template -f ${k8s_root_path}/${dev_prod_mode}/core.yaml web ${template_folder} --output-dir  ${manifest_save_path}/${dev_prod_mode}/web
helm template -f ${k8s_root_path}/${dev_prod_mode}/pp.yaml pp ${template_folder} --output-dir  ${manifest_save_path}/${dev_prod_mode}/pp


