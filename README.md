# flask-app

INVENTORY MANAGEMENT USING FLASK AND MYSQL DATABASE IN K8S ENVIRONMENT ON LOCAL MACHINE
Prerequisite :
1.VM Installed with Kubeadm Cluster
2. VM Installed as slave node to cluster 
3. Deploy Jenkins - master pod in Control-Plane (can have persistent storage for reusable jobs files and credentials)
4. Deploy Jenkins - agent pod in Control-Plane
(Installed jenkins agent pod should have docker-cli and kubectl installed and ssh deamon running in background )
5. Create required directory path and specified storage size in slave node for Mysql-pod for persistent storage of database
Directory Structure : 

<img width="975" height="318" alt="image" src="https://github.com/user-attachments/assets/20b215d0-66c5-4801-827c-9b8b1bb7e180" />


Git Project Link: https://github.com/nitin3-cmy2k/flask-app.git
Post running the Jenkins pipeline successfully we will have the dashboard as shown below

Dashboard Page of Inventory app 

<img width="975" height="514" alt="image" src="https://github.com/user-attachments/assets/c5cb48fd-fcdc-4405-994d-efea1057a383" />
