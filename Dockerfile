FROM ubuntu:12.04
RUN apt-get update
RUN apt-get install -y openssh-server software-properties-common wget subversion python-software-properties openjdk-7-jre-headless gcc build-essential yasm pkg-config lsof git
ADD . /home/unveillance
WORKDIR /home/unveillance
RUN rm Dockerfile
RUN chmod +x setup.sh