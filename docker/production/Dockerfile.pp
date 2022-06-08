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

RUN apt-get -qq update && \
    apt-get -y -qq install locales && \
    locale-gen ko_KR.UTF-8

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y -qq install \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmysqlclient-dev \
    python3-pip \
    python3-venv \
    tzdata

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

COPY ./requirements/pp/pyproject.toml /workspace/
COPY ./requirements/pp/poetry.lock /workspace/

WORKDIR /workspace

RUN poetry install --no-dev

COPY ./.env.prod /workspace/.env

RUN rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache && \
    rm -rf /usr/bin/gcc

RUN groupadd -r lomin -g 1000 && \
    useradd -u 1000 -r -g lomin -s /sbin/nologin -c "Docker image user" textscope

USER textscope

WORKDIR /workspace/pp_server
