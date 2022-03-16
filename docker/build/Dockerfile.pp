ARG UBUNTU_VERSION
ARG POETRY_VERSION

FROM ubuntu:${UBUNTU_VERSION}

ARG BASE_PATH
ARG LINUX_ENV_PATH
ARG DEMOMA_PATH
ARG SO_EXTENTION
ARG USER

# RUN groupadd -r ${USER} && useradd --no-log-init -r -g ${USER} ${USER}

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="$PYTHONPATH:/workspace"

RUN apt-get -qq update && \
    apt-get -y -qq install locales && \
    locale-gen ko_KR.UTF-8

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y -qq install git \
    python3-pip \
    python3-venv \
    tzdata \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libmysqlclient-dev \
    libprotobuf-dev \
    protobuf-compiler \
    cmake \
    curl


# ARG TEXTSCOPE_BASE_IMAGE_VERSION

# FROM docker.lomin.ai/ts-pp-base:${TEXTSCOPE_BASE_IMAGE_VERSION}

# ARG BASE_PATH
# ARG LINUX_ENV_PATH
# ARG DEMOMA_PATH
# ARG SO_EXTENTION
# ARG USER

# # RUN groupadd -r ${USER} && useradd --no-log-init -r -g ${USER} ${USER}

# ENV LC_ALL=C.UTF-8
# ENV LANG=C.UTF-8
# ENV PYTHONPATH="$PYTHONPATH:/workspace"
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 - && \
    echo "PATH=/root/.local/bin:$PATH" > /etc/environment && \
    poetry config virtualenvs.create false

COPY ./lovit/lovit/ /workspace/lovit/
COPY ./pp_server /workspace/pp_server
COPY ./assets/thales/ /workspace/assets/thales
COPY ./.env /workspace/.env
COPY ./requirements/pp/pyproject.toml /workspace/
COPY ./requirements/pp/poetry.lock /workspace/

WORKDIR /workspace

RUN pip3 install --upgrade pip
RUN poetry install

RUN git clone https://github.com/Nuitka/Nuitka.git && \
    cd Nuitka && \
    python3 setup.py install

RUN python3 -m nuitka --module lovit --include-package=lovit && \
    find lovit/* -maxdepth 0 -name 'resources' -prune -o -exec rm -rf '{}' ';'

# RUN ${LINUX_ENV_PATH} -v:${DEMOMA_PATH} -f:100 --dfp lovit.${SO_EXTENTION} lovit.${SO_EXTENTION}

WORKDIR /workspace/pp_server
RUN mv pp_server/app/main.py ./main.py && \
    python3 -m nuitka --module pp_server --include-package=pp_server

# RUN ${LINUX_ENV_PATH} -v:${DEMOMA_PATH} -f:100 --dfp pp_server.${SO_EXTENTION} pp_server.${SO_EXTENTION}

RUN rm -rf /workspace/pp_server/pp_server /workspace/assets /workspace/*.txt&& \
    rm -f /workspace/pyproject.toml /workspace/poetry.lock && \
    rm -rf /workspace/Nuitka /workspace/pp_server/*.build && \
    rm -rf /var/lib/apt/lists/*
