FROM ctfd/ctfd:latest

# Elevate to root.
USER 0

#Setup plugin in CTFd image.
COPY . /opt/CTFd/CTFd/plugins/kubernetes
WORKDIR /opt/CTFd/CTFd/plugins/kubernetes
RUN rm -f ./GETTING-STARTED.md
RUN rm -f ./README.md
RUN rm -f ./*.sh
RUN rm -f ./*.png

# Install Python requirements for plugin.
RUN pip install -r ./requirements.txt

# Back to original CTFd image usage.
WORKDIR /opt/CTFd
RUN chmod +x /opt/CTFd/docker-entrypoint.sh \
    && chown -R 1001:1001 /opt/CTFd /var/log/CTFd /var/uploads
USER 1001
