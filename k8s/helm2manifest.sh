# USAGE sh helm2manifest.sh {develop or production}
if [ $# -eq 0 ] ; then
    echo "Warning: no arguments"
    exit 0
fi
dev_prod_mode=$1

# helm template -f {헬름 value yaml 파일} {service name} {템플릿 경로} --output-dir {저장 위치}
helm template -f values/${dev_prod_mode}/minio.yaml textscope-minio bitnami/minio --output-dir manifest/${dev_prod_mode}/minio
helm template -f values/${dev_prod_mode}/postgresql.yaml textscope-postgresql bitnami/postgresql --output-dir  manifest/${dev_prod_mode}/postgresql

helm template -f values/${dev_prod_mode}/wrapper.yaml textscope-wrapper textscope --output-dir  manifest/${dev_prod_mode}/wrapper
helm template -f values/${dev_prod_mode}/serving.yaml textscope-serving textscope --output-dir  manifest/${dev_prod_mode}/serving
helm template -f values/${dev_prod_mode}/core.yaml textscope-web textscope --output-dir  manifest/${dev_prod_mode}/web
helm template -f values/${dev_prod_mode}/pp.yaml textscope-pp textscope --output-dir  manifest/${dev_prod_mode}/pp


