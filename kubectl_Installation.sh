export KUBERNETES_VERSION=v1.33
echo "Add Kubernetes repository and GPG key"

curl -fsSL https://pkgs.k8s.io/core:/stable:/$KUBERNETES_VERSION/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/$KUBERNETES_VERSION/deb/ /" | tee /etc/apt/sources.list.d/kubernetes.list

echo "Update package lists and install CRI-O along with Kubernetes components"
apt-get update -y
apt-get install -y  kubectl
sudo apt-mark hold kubectl
