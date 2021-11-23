#!/bin/bash

read -p "Where must CTFd be installed? (absolute or relative path is accepted.): " path

absolute_path=$(realpath $path)

if [ -d $path ]
then
    echo "Directory $absolute_path exists."
    cd $path
else
    echo "Error: Directory $absolute_path doesn't exist."
    exit 1
fi

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Linux found"
  echo "Installing virtualenv for Debian based systems"
  sudo apt install -y python3-virtualenv > /dev/null
elif [[ "$OSTYPE" == "darwin"* ]]; then
  echo "MacOS found"
  echo "Installing virtualenv for MacOS"
  pip install virtualenv > /dev/null
else
  echo "Error: No compatible OS found."
  exit 1
fi

echo "--Installing CTFd--"
echo "Cloning official CTFd"
git clone https://github.com/CTFd/CTFd.git > /dev/null
cd ./CTFd
echo "Creating virtual environment"
virtualenv env/ > /dev/null
source ./env/bin/activate
echo "Installing pip requirements"
pip install -r ./requirements.in > /dev/null

cd ./CTFd/plugins/
echo "--Installing Kubernetes plugin--"
echo "Cloning Kubernetes plugin"
git clone https://github.com/MVDB0110/CTFd-Kubernetes > /dev/null
mv CTFd-Kubernetes kubernetes
rm -rf ./kubernetes/.git
echo "Installing Kuberntes pip requirements"
pip install -r kubernetes/requirements.txt > /dev/null

cd ../../
echo "Starting CTFd"
flask run -h 0.0.0.0
