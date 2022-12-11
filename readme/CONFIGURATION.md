# Configuration Upload

In order to upload container-based challenges to CTFd, the container challenges plugin must be configured correctly. There are 2 steps that need to be taken:

1. Upload container registry url
2. Upload container registry password
3. Upload container registry username
4. Upload infrastructure image

## 1. Container registry Username/Password

The container challenges plugin needs to be able to access your challenge images. However, the container registry is private so it needs credentials to gain access. Container registry credentials are in the form of a username and deploy token.