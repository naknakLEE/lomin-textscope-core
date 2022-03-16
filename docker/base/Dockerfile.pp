ARG UBUNTU_VERSION
ARG POETRY_VERSION

FROM ubuntu:${UBUNTU_VERSION}

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHONPATH="$PYTHONPATH:/workspace/pp_server"
ENV API_ENV="production"
ENV PATH="/root/.local/bin:${PATH}"

RUN apt-get -qq update && \
    apt-get -y -qq install locales && \
    locale-gen ko_KR.UTF-8

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y -qq install git \
    python3-pip \
    python3-venv \
    tzdata \
    libgl1-mesa-glx libglib2.0-0 \
    libmysqlclient-dev \
    curl

RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3 - && \
    echo "PATH=/root/.local/bin:$PATH" > /etc/environment && \
    poetry config virtualenvs.create false

RUN pip3 install --upgrade pip

WORKDIR /workspace
RUN pip3 install torch==1.8.1+cpu torchvision==0.9.1+cpu -f https://download.pytorch.org/whl/torch_stable.html

COPY ./requirements/pp/pyproject.toml /workspace/
COPY ./requirements/pp/poetry.lock /workspace/
RUN poetry install

WORKDIR /workspace/lovit
COPY ./lovit /workspace/lovit
RUN python3 setup.py build develop && \
    rm -rf /workspace/lovit

COPY ./.env /workspace/

RUN groupadd -r lomin -g 1000 && \
    useradd -u 1000 -r -g lomin -s /sbin/nologin -c "Docker image user" textscope

USER textscope

WORKDIR /workspace/pp_server/pp_server/app

ENTRYPOINT ["python3", "main.py"]
