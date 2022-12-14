ARG UBUNTU_VERSION

FROM ubuntu:${UBUNTU_VERSION}

ARG BUILD_FOLDER_PATH
ARG CUSTOMER
ARG MAINTAINER
ARG POETRY_VERSION

LABEL maintainer=${MAINTAINER}

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="$PYTHONPATH:/workspace/pp_server"
ENV API_ENV="production"
ENV DOCKER_ENV="True"

RUN apt-get -qq update

RUN apt-get -y -qq install locales && \
    locale-gen ko_KR.UTF-8

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y -qq install \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmysqlclient-dev \
    python3-pip \
    python3-venv \
    tzdata \
    g++ \
    openjdk-8-jdk \
    python3-dev

# RUN pip3 install --upgrade pip

RUN pip3 install \
    torch==1.8.1+cpu \
    torchvision==0.9.1+cpu -f https://download.pytorch.org/whl/torch_stable.html

RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 - && \
    echo "PATH=/root/.local/bin:$PATH" > /etc/environment && \
    poetry config virtualenvs.create false

COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}/lovit/lovit.cpython-38-x86_64-linux-gnu.so /workspace/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}/lovit/lovit.pyi /workspace/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}/lovit/lovit /workspace/lovit/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}/pp/pp.cpython-38-x86_64-linux-gnu.so /workspace/pp_server/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}/pp/pp.pyi /workspace/pp_server/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}/pp/main.py /workspace/pp_server/
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}/pp/assets /workspace/pp_server/assets
COPY ./${BUILD_FOLDER_PATH}/${CUSTOMER}/assets/textscope.json /workspace/assets/textscope.json

COPY ./pp_server/lovit/requirements.txt /workspace/pp_server/lovit/requirements.txt
COPY ./pp_server/requirements/pyproject.toml /workspace/
COPY ./pp_server/requirements/poetry.lock /workspace/

WORKDIR /workspace

RUN pip3 install -r /workspace/pp_server/lovit/requirements.txt
RUN poetry install --no-dev

COPY ./.env.prod /workspace/.env

RUN rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache && \
    rm -rf /usr/bin/gcc

USER root
RUN echo "export DEPLOY_DATE=$(date +'%Y-%m-%d')" >> /etc/bash.bashrc

RUN groupadd -r lomin -g 1000 && \
    useradd -u 1000 -r -g lomin -s /sbin/nologin -c "Docker image user" textscope

USER textscope

WORKDIR /workspace/pp_server
