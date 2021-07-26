ARG UBUNTU_VERSION

FROM ubuntu:${UBUNTU_VERSION}

ARG BASE_PATH
ARG LINUX_ENV_PATH
ARG DEMOMA_PATH
ARG SO_EXTENTION
ARG USER

RUN groupadd -r ${USER} && useradd --no-log-init -r -g ${USER} ${USER}

ENV PYTHONPATH="$PYTHONPATH:/workspace"

RUN apt-get update && \
    apt-get install -y git && \
    apt-get -y install python3-pip && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt-get -y install libgl1-mesa-glx libglib2.0-0 && \
    apt-get -y install libmysqlclient-dev && \
    apt-get install -y libprotobuf-dev protobuf-compiler && \
    apt-get -y install cmake

RUN rm -rf /var/lib/apt/lists/*

COPY ./lovit /workspace/lovit
COPY ./pp_server /workspace/pp_server
COPY ./assets/thales/ /workspace/assets/thales
COPY ./.env /workspace/.env
COPY ./requirments/requirments-pp.txt /workspace/requirments-pp.txt

RUN pip3 install --upgrade pip && \
    pip3 install -r /workspace/requirments-pp.txt

WORKDIR /workspace/lovit
RUN python3 setup.py install && \
    rm -r /workspace/lovit

WORKDIR /workspace
RUN git clone https://github.com/Nuitka/Nuitka.git && \
    cd Nuitka && \
    python3 setup.py install

WORKDIR /workspace/pp_server
RUN mv pp_server/app/main.py ./main.py && \
    python3 -m nuitka --module pp_server --include-package=pp_server && \
    ${LINUX_ENV_PATH} -v:${DEMOMA_PATH} -f:100 --dfp pp_server.${SO_EXTENTION} pp_server.${SO_EXTENTION}

RUN rm -r /workspace/pp_server/pp_server /workspace/assets /workspace/requirments-pp.txt&& \
    rm -r /workspace/Nuitka /workspace/pp_server/pp_server.build

# ENTRYPOINT ["python3", "main.py"]

# WORKDIR /workspace/pp_server/app
# RUN mkdir -p  soynlp/noun && \
#     cp -r /usr/local/lib/python3.8/dist-packages/soynlp/noun/ /workspace/pp_server/app/dist/main/soynlp/

