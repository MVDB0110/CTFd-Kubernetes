# CTFd-Kubernetes
Getting started with container-based challenges

## 1. Features

- Container registry configuration
- Uploading Docker challenges
- Converting Docker challenges
- Deploying Docker challenges in Kubernetes
- Destroying Docker challenges in Kubernetes
- Kubernetes namespace management

## 2. Instructions container-based challenge

1. Create a dockerfile for the container(s) you want to include in the challenge. Note: All necessary files that it interacts with, must be included in the image.
2. Build and try your image. When you're satisfied, upload the container image to a container registry.
3. Package it all up as a docker-compose file and test. If it works, you can encode your docker-compose file
4. Upload the challenge and test if the deployment and flag input work. Export your static and container-based challenges and share it with somebody to solve.

