ARG UBUNTU_VERSION=18.04

FROM ubuntu:${UBUNTU_VERSION} 

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHONPATH="$PYTHONPATH:/workspace"
ENV API_ENV="production"

RUN apt-get update && \
    apt-get install -y git  && \
    apt-get install -y locales && \
    locale-gen ko_KR.UTF-8 && \
    apt-get -y install python3-pip && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt-get -y install libgl1-mesa-glx libglib2.0-0 && \
    apt-get -y install libmysqlclient-dev

RUN pip3 install --upgrade pip

WORKDIR /workspace
RUN git clone https://github.com/Nuitka/Nuitka.git && \
    cd Nuitka && \
    python3 setup.py install


COPY ./requirments/requirments-pp.txt /workspace/
RUN pip3 install -r /workspace/requirments-pp.txt

COPY ./lovit /workspace/lovit
WORKDIR /workspace/lovit
RUN python3 setup.py install && \
    rm -rf /workspace/lovit

COPY ./.env /workspace/

RUN rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

WORKDIR /workspace/pp_server
# ENTRYPOINT ["python3", "main.py"]
