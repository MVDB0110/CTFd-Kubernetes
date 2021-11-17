# CTFd-Kubernetes
Getting started - Container Challenges
Getting started with container-based challenges

Make your own CTF challenge
Try to think of a basic CTF challenge that somebody else must be able to solve.

Design and make a static text or upload based challenge first and save it in CTFd.
Move on to creating a container-based challenge.


Instructions container-based challenge
1. Create a dockerfile for the container(s) you want to include in the challenge. Note: All necessary files that it interacts with, must be included in the image.
2. Build and try your image. When you're satisfied, upload the container image to a container registry.
3. Package it all up as a docker-compose file and test. If it works, you can encode your docker-compose file
4. Upload the challenge and test if the deployment and flag input work. Export your static and container-based challenges and share it with somebody to solve.

![image info](/deployed-challenge.png "Deployed challenge")
