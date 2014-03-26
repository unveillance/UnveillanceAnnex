FROM ubuntu:12.04
RUN apt-get update
RUN apt-get install -y openssh-server software-properties-common wget subversion python-software-properties
RUN add-apt-repository ppa:fmarier/git-annex
RUN apt-get update
RUN apt-get install -y gcc build-essential yasm pkg-config python-dev lsof python-pip git git-annex
ADD . /home/unveillance
WORKDIR /home/unveillance
RUN rm Dockerfile
RUN chmod +x setup.sh