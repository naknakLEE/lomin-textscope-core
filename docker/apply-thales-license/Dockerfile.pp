ARG UBUNTU_VERSION

FROM ubuntu:${UBUNTU_VERSION} 

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHONPATH="$PYTHONPATH:/workspace"

RUN apt-get update && \
    apt-get -y install python3-pip && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt-get -y install libgl1-mesa-glx libglib2.0-0 && \
    apt-get -y install libmysqlclient-dev

COPY --from=builder /workspace/lovit.cpython-36m-x86_64-linux-gnu.so /workspace/
COPY --from=builder /workspace/lovit.pyi /workspace/
COPY --from=builder /workspace/.env /workspace/
COPY --from=builder /workspace/requirments-pp.txt /workspace/
COPY --from=builder /workspace/pp_server/pp_server.cpython-36m-x86_64-linux-gnu.so /workspace/pp_server/
COPY --from=builder /workspace/pp_server/pp_server.pyi /workspace/pp_server/
COPY --from=builder /workspace/pp_server/main.py /workspace/pp_server/

RUN pip3 install --upgrade pip && \
    pip3 install -r /workspace/requirments-pp.txt

RUN rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

# ENTRYPOINT ["python3", "main.py"]
