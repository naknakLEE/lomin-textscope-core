# Start local cluster
minikube start

# Set textscope context
kubectl config set-context --current --namespace=textscope

# Create namespace
kubectl apply -f k8s/namespace.yaml
# Create textscope service
kubectl apply -f k8s/textscope.yaml
# Create monitoring service
kubectl apply -f k8s/monitoring.yaml
# Create istio gateway
kubectl apply -f k8s/istio_gateway.yaml