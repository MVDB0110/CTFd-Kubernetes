export REGISTRY_USERNAME=$1
export REGISTRY_PASSWORD=$2
export REGISTRY_EMAIL=$3
export BASE64_CREDENTIALS=$(echo "$REGISTRY_USERNAME:$REGISTRY_PASSWORD" | base64 -w 0)
export BASE64_DOCKERCONFIGJSON=$(echo "{\"auths\": {\"https://registry.gitlab.com\": {\"username\": \"$REGISTRY_USERNAME\", \"password\": \"$REGISTRY_PASSWORD\", \"email\": \"$REGISTRY_EMAIL\", \"auth\": \"$BASE64_CREDENTIALS\"}}}" | base64 -w 0)
echo $BASE64_DOCKERCONFIGJSON
