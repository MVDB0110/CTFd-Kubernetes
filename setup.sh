#!/bin/bash

cd $1

pip install virtualenv
git clone https://github.com/CTFd/CTFd.git
cd ./CTFd
virtualenv env/
source ./env/bin/activate
pip install -r ./requirements.in

cd ./CTFd/plugins/
git clone https://github.com/MVDB0110/CTFd-Kubernetes
mv CTFd-kubernetes kubernetes
rm -rf ./kubernetes/.git
pip install -r kubernetes/requirements.txt

cd ../../
flask run -h 0.0.0.0