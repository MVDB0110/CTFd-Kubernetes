# 1. CTFd-Kubernetes-plugin

This plugin makes it possible to deploy challenges as a container environment for every ctf attendee. This plugin is intended for plug & play use. The flow which this plugin works by consists of 4 steps. The first step is to create the namespace for the user. The namespace gets the name of "ctf-user-{user-id}-{challenge-id}". This name is for the isolation of users and their challenges from other users. The second step is to create a serviceaccount and secret. This step is for the rights that the deployment container needs. The rights consists of Kubernetes API rights and the right to use the private container registry. The second one may become optional in the future but is required for now. The third step is where a Kubernetes Job is created. CTFd listens to this job for its completion and reports back to the browser. The last step is to request the required information of the Kubernetes cluster for the completion of the challenge (eq. nodePort, host information). After each call to one of the endpoints, the clients browser will receive a 201 or 409. In case of 201 everything went okay. In case of 409 you get a Kubernetes API response from the endpoint in the response of your call to CTFd.

- [1. CTFd-Kubernetes-plugin](#1-ctfd-kubernetes-plugin)
  - [1.1. Preparation](#11-preparation)
  - [1.2. Installation](#12-installation)
    - [1.2.1. Dev-machine](#121-dev-machine)
    - [1.2.2. Kubernetes](#122-kubernetes)
    - [1.2.3. Configuration values](#123-configuration-values)
- [2. Appendix](#2-appendix)
  - [2.1 RBAC](#21-rbac)

## 1.1. Preparation

Make sure the node that will make API calls to Kubernetes has access to Kubernetes [Kubectl](https://kubernetes.io/docs/tasks/tools/). In case of in-cluster CTFd you don't have to setup kubectl.

## 1.2. Installation

### 1.2.1. Dev-machine

> It is strongly recommended you install all the requirements in a virtual environment [Virtualenv](https://virtualenv.pypa.io/en/latest/installation.html).

```Bash
pip install virtualenv
cd /path/to/CTFd-root
virtualenv env/
source ./env/bin/activate
```

Make sure you install all requirements for CTFd through pip on the machine or in your virtual environment:
```Bash
cd /path/to/CTFd-root
pip install -r ./requirements.in
```

After installation of the pip requirement you can place the contents of the repository under: "CTFd/plugins/kubernetes/". The contents can be downloaded either through git clone:
```Bash
cd /path/to/CTFd-root/CTFd/plugins/
git clone https://github.com/MVDB0110/CTFd-Kubernetes
mv CTFd-Kubernetes kubernetes
rm -rf ./kubernetes/.git
pip install -r kubernetes/requirements.txt
```
Or by downloading the source code of master through the browser. Lastly you can proceed to start CTFd like you usually would on the local machine. NOTE: do not connect to CTFd using "localhost" or "127.0.0.1". Instead use the IP-adres of the local-machine, which the device has got from your router (eq. 192.168.2.25).

```Bash
cd /path/to/CTFd-root
flask run -h 0.0.0.0
```

### 1.2.2. Kubernetes

In the case of in-cluster deployment of this plugin you can follow this part.
To do this you can apply the definition files in k8-definition, this map can be found in this repository:
> This adds a namespace. In this namespace the following deployments are created: ctfd, db, cache.
```Bash
cd /path/to/k8-definition
kubectl apply -f .
```
Now you can connect to CTFd using a NodePort. If you want to use an ingress resource you must add this yourself.

### 1.2.3. Configuration values

This plugin has two values which can be edited through the CTFd admin panel. The page in the admin panel can be found under Admin Panel > Plugins > Kubernetes.

- Container Image
- Registry Secret

The container image is the image which will be used as deployment image. The prebuild container image for the deployment image is: "ghcr.io/mvdb0110/ctfd-kubernetes-container:master". If you want to build this image yourself, use the following link [CTFd-Kubernetes-container](https://github.com/MVDB0110/CTFd-kubernetes-container). <br />

The registry secret is a base 64 representation of the .dockerconfigjson file. The exact structure can be read in the Kubernetes documentation. The structure used by the developer is:

```Bash
{"auths": {"https://registry.gitlab.com": {"username": "username", "password": "password", "email": "example@github.com", "auth": "base64(username:password)"}}}
```

This hash needs to be base 64 encoded with UTF-8.

# 2. Appendix
## 2.1 RBAC

The following resources in Kubernetes need to be in order for the plugin to work. The service account will be bound to CTFd. All of these resources need to be created in the same namespace as CTFd. This is applied in the k8-definition map under ctfd-deployment.yaml
```Bash
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {serviceaccount}
  namespace: {namespace}
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: {clusterrole}
rules:
- apiGroups: ["", "apps", "batch", "rbac.authorization.k8s.io"]
  resources: ["pods", "namespaces", "services", "deployments", "jobs", "roles", "rolebindings", "nodes", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "watch", "delete", "deletecollection"]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: {clusterrolebinding }
subjects:
- kind: ServiceAccount
  name: {service account}
  namespace: {namespace}
roleRef:
  kind: ClusterRole
  name: {clusterrole}
  apiGroup: rbac.authorization.k8s.io
```
