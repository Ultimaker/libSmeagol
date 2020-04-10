FROM registry.hub.docker.com/library/debian:buster-slim

RUN apt-get update && apt-get -y install cmake make python3 python3-pip git

COPY docker_env/buildenv_check.sh buildenv_check.sh

COPY smeagol_requirements.txt smeagol_requirements.txt

RUN pip3 install -r smeagol_requirements.txt
