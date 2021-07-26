FROM ubuntu:18.04

ENV PYTHONPATH="$PYTHONPATH:/workspace"

RUN apt-get update && \
    apt-get install -y git && \
    apt-get -y install python3-pip && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata && \
    apt-get -y install libgl1-mesa-glx libglib2.0-0 && \
    apt-get -y install libmysqlclient-dev && \
    apt-get install -y libprotobuf-dev protobuf-compiler && \
    apt-get -y install cmake

COPY ./lovit /workspace/lovit
COPY ./pp_server/pp_server /workspace/pp_server
COPY ./.env /workspace/.env
COPY ./requirments/requirments-pp.txt /workspace/requirments-pp.txt

RUN pip3 install --upgrade pip && \
    pip3 install -r /workspace/requirments-pp.txt

# WORKDIR /workspace/lovit
# RUN python3 setup.py install && \
#     rm -r /workspace/lovit

# WORKDIR /workspace
# RUN git clone https://github.com/Nuitka/Nuitka.git && \
#     cd Nuitka && \
#     python3 setup.py install

# RUN mv pp_server/app/main.py ./main.py && \
#     python3 -m nuitka --module pp_server --include-package=pp_server && \
#     python3 -m nuitka main.py

# RUN rm -r pp_server Nuitka main.py

# WORKDIR /workspace/pp_server/app
# RUN mkdir -p  soynlp/noun && \
#     cp -r /usr/local/lib/python3.8/dist-packages/soynlp/noun/ /workspace/pp_server/app/dist/main/soynlp/

