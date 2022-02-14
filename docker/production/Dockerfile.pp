ARG UBUNTU_VERSION

FROM ubuntu:${UBUNTU_VERSION}

ARG BUILD_FOLDER_PATH
ARG CUSTOMER
ARG MAINTAINER

LABEL maintainer=${MAINTAINER}

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHONPATH="$PYTHONPATH:/workspace/pp_server"
ENV API_ENV="production"

RUN apt-get update && \
    apt-get install -y locales && \
    locale-gen ko_KR.UTF-8 && \
    apt-get -y install python3-pip && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt-get -y install libgl1-mesa-glx libglib2.0-0 && \
    apt-get -y install libmysqlclient-dev

RUN pip3 install --upgrade pip

COPY ./requirments/requirments-pp.txt /workspace/
RUN pip3 install -r /workspace/requirments-pp.txt

COPY ./.env /workspace/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}-build/lovit/lovit.cpython-36m-x86_64-linux-gnu.so /workspace/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}-build/lovit/lovit.pyi /workspace/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}-build/lovit/lovit /workspace/lovit/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}-build/pp/pp_server.cpython-36m-x86_64-linux-gnu.so /workspace/pp_server/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}-build/pp/pp_server.pyi /workspace/pp_server/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}-build/pp/main.py /workspace/pp_server/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}-build/assets/* /workspace/assets/

RUN rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache && \
    rm -rf /usr/bin/gcc

WORKDIR /workspace/pp_server
# ENTRYPOINT ["python3", "main.py"]
