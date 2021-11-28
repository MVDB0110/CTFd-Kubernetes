#!/bin/bash
#Syntax: ./base64.sh registry-url username password email
export REGISTRY_URL=$1
export REGISTRY_USERNAME=$2
export REGISTRY_PASSWORD=$3
export REGISTRY_EMAIL=$4
export BASE64_CREDENTIALS=$(echo "$REGISTRY_USERNAME:$REGISTRY_PASSWORD" | base64 -w 0)
export BASE64_DOCKERCONFIGJSON=$(echo "{\"auths\": {\"$REGISTRY_URL\": {\"username\": \"$REGISTRY_USERNAME\", \"password\": \"$REGISTRY_PASSWORD\", \"email\": \"$REGISTRY_EMAIL\", \"auth\": \"$BASE64_CREDENTIALS\"}}}" | base64 -w 0)
echo $BASE64_DOCKERCONFIGJSON
