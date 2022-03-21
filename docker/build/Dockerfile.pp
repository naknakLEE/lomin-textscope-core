ARG TEXTSCOPE_BASE_IMAGE_VERSION
ARG UBUNTU_VERSION
ARG POETRY_VERSION

FROM docker.lomin.ai/ts-pp-base:${TEXTSCOPE_BASE_IMAGE_VERSION}

ARG BASE_PATH
ARG LINUX_ENV_PATH
ARG DEMOMA_PATH
ARG SO_EXTENTION
ARG USER
ARG PYTHON_VERSION

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PATH="/root/.local/bin:${PATH}"
ENV PYTHONPATH="$PYTHONPATH:/workspace"

USER 0

COPY ./lovit/lovit/ /workspace/lovit/
COPY ./pp_server /workspace/pp_server
COPY ./assets/thales/ /workspace/assets/thales
COPY ./.env /workspace/.env
COPY ./requirements/pp/pyproject.toml /workspace/
COPY ./requirements/pp/poetry.lock /workspace/

WORKDIR /workspace
RUN sed -i 's/# Support for gcc and clang, restricting visibility as much as possible./env.Append(CCFLAGS=["-fcf-protection=none"])/' /usr/local/lib/python${PYTHON_VERSION}/dist-packages/nuitka/build/SconsCompilerSettings.py
RUN python3 -m nuitka --module lovit --include-package=lovit && \
    find lovit/* -maxdepth 0 -name 'resources' -prune -o -exec rm -rf '{}' ';'

WORKDIR /workspace/pp_server
RUN mv pp_server/app/main.py ./main.py && \
    python3 -m nuitka --module pp_server --include-package=pp_server

RUN rm -rf /workspace/pp_server/pp_server /workspace/assets /workspace/*.txt&& \
    rm -f /workspace/pyproject.toml /workspace/poetry.lock && \
    rm -rf /workspace/Nuitka /workspace/pp_server/*.build && \
    rm -rf /var/lib/apt/lists/*
