# Inventory Management System on Local Kubernetes (Kubeadm)

A containerized Flask and MySQL Inventory Management application deployed on a local multi-node Kubeadm cluster using an automated Jenkins CI/CD pipeline.

# Architecture Overview
 Control-Plane Node: Hosts the Kubernetes control plane, Jenkins Master pod (with persistent storage), and Jenkins SSH Agent pod (equipped with `docker-cli` and `kubectl`).
 Worker (Slave) Node: Hosts the MySQL database pod (backed by a Local PersistentVolume at `/mnt/data/mysql`) and Flask web application replicas.

# Prerequisites
1. Kubeadm Cluster: At least 1 Control-Plane VM and 1 Worker (Slave) VM in `Ready` state.
2. Worker Storage: Local directory `/mnt/data/mysql` created on the Worker node.
3. Jenkins Setup: Jenkins Master and SSH Agent pods deployed on the Control-Plane node.
4. Container Registry: Docker Hub account (or local registry) configured in Jenkins credentials as `dockerhub-creds`.

# Setup & Deployment Instructions

# Step 1: Prepare Storage on Worker Node
Log into the Worker node and run:

sudo mkdir -p /mnt/data/mysql && 
sudo chmod 777 /mnt/data/mysql

# Step 2: Deploy Jenkins Master & Agent
add jenkins-agents username password in Jenkins Dashboard

Access Jenkins UI at `http://<CONTROL_PLANE_IP>:30080` and connect the agent node via `jenkins-agent-svc` on port `22`.

# Step 3: Update Manifest Placeholders
 In `k8s/mysql/mysql-pv-pvc.yaml`, replace `<WORKER_NODE_HOSTNAME>` with your worker node name (`kubectl get nodes`).
 In `k8s/flask/flask-deployment.yaml` and `Jenkinsfile`, replace `<YOUR_DOCKERHUB_USERNAME>` with your registry username.

# Step 4: Run the Jenkins Pipeline
1. Create a new Pipeline job in Jenkins pointing to this Git repository.
2. Trigger Build Now to build the Flask image, push it to the registry, and deploy MySQL and Flask to Kubernetes.

# Step 5: Access the Application

Open your browser and navigate to:

http//masternode:30500

Post running the Jenkins pipeline successfully we will have the dashboard as shown below

Dashboard Page of Inventory app 

<img width="975" height="514" alt="image" src="https://github.com/user-attachments/assets/c5cb48fd-fcdc-4405-994d-efea1057a383" />
