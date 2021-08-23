ARG UBUNTU_VERSION

FROM ubuntu:${UBUNTU_VERSION} as builder

ARG BASE_PATH
ARG LINUX_ENV_PATH
ARG DEMOMA_PATH
ARG SO_EXTENTION
ARG USER

# RUN groupadd -r ${USER} && useradd --no-log-init -r -g ${USER} ${USER}

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHONPATH="$PYTHONPATH:/workspace"

RUN apt-get update && \
    apt-get install -y git && \
    apt-get -y install python3-pip && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt-get -y install libgl1-mesa-glx libglib2.0-0 && \
    apt-get -y install libmysqlclient-dev && \
    apt-get install -y libprotobuf-dev protobuf-compiler && \
    apt-get -y install cmake

WORKDIR /workspace
RUN git clone https://github.com/Nuitka/Nuitka.git && \
    cd Nuitka && \
    python3 setup.py install

RUN pip3 install --upgrade pip
