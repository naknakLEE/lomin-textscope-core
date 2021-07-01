FROM textscoperegistry.azurecr.io/opencv_base_image:ubuntu20.04

ENV PYTHONPATH="$PYTHONPATH:/workspace"

RUN apt-get install -y git

COPY ./ /tmp

RUN mkdir /workspace && \
    mv /tmp/lovit /workspace/lovit && \
    mv /tmp/app /workspace/app && \
    mv /tmp/pp_server /workspace/pp_server && \
    mv /tmp/.env /workspace/.env && \
    mv /tmp/requirments/requirments-pp.txt /workspace/requirments-pp.txt && \
    rm -r /tmp

RUN pip3 install -r /workspace/requirments-pp.txt

WORKDIR /workspace/lovit
RUN python3 setup.py install && \
    rm -r /workspace/lovit

WORKDIR /workspace

# WORKDIR /workspace
# RUN git clone https://github.com/Nuitka/Nuitka.git && \
#     cd Nuitka && \
#     python3 setup.py install

# RUN mv pp_server/main.py ./main.py && \
#     python3 -m nuitka --module pp_server --include-package=pp_server && \
#     rm -r pp_server Nuitka
