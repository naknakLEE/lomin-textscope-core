ARG UBUNTU_VERSION

FROM ubuntu:${UBUNTU_VERSION} 

ARG ENCRYPTED_PATH

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHONPATH="$PYTHONPATH:/workspace"
ENV API_ENV="production"

RUN apt-get update && \
    apt-get -y install python3-pip && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt-get -y install libgl1-mesa-glx libglib2.0-0 && \
    apt-get -y install libmysqlclient-dev

RUN pip3 install --upgrade pip

COPY ./.env /workspace/
COPY ./${ENCRYPTED_PATH}/lovit/lovit.cpython-36m-x86_64-linux-gnu.so /workspace/
COPY ./${ENCRYPTED_PATH}/lovit/lovit.pyi /workspace/
COPY ./requirments/requirments-pp.txt /workspace/
COPY ./${ENCRYPTED_PATH}/pp/pp_server.cpython-36m-x86_64-linux-gnu.so /workspace/pp_server/
COPY ./${ENCRYPTED_PATH}/pp/pp_server.pyi /workspace/pp_server/
COPY ./${ENCRYPTED_PATH}/pp/main.py /workspace/pp_server/

RUN pip3 install -r /workspace/requirments-pp.txt

RUN rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

WORKDIR /workspace/pp_server
# ENTRYPOINT ["python3", "main.py"]
