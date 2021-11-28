FROM ctfd/ctfd:latest

COPY . /opt/CTFd/CTFd/plugins/kubernetes

WORKDIR /opt/CTFd/CTFd/plugins/kubernetes

RUN rm -f ./GETTING-STARTED.md
RUN rm -f ./README.md
RUN rm -f ./*.sh
RUN rm -f ./*.png

RUN pip install -r ./requirements.txt

ENTRYPOINT ["/opt/CTFd/docker-entrypoint.sh"]
