# Start local cluster
minikube start

# Set textscope context
kubectl config set-context --current --namespace=textscope

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create textscope service
helm install -f k8s/values/wrapper.yaml wrapper k8s/textscope
helm install -f k8s/values/pp.yaml pp k8s/textscope
helm install -f k8s/values/core.yaml core k8s/textscope
helm install -f k8s/values/serving.yaml serving k8s/textscope

helm install -f k8s/values/elasticsearch.yaml elasticsearch elastic/elasticsearch --version 7.16.3
helm install -f k8s/values/postgresql.yaml postgresql bitnami/postgresql --version 11.0.3
helm install -f k8s/values/prometheus.yaml prometheus prometheus-community/prometheus --version 15.3.0

kubectl apply -f k8s/ldap.yaml

# Create monitoring service
kubectl apply -f k8s/monitoring.yaml

# Create istio gateway
kubectl apply -f k8s/istio_gateway.yaml