FROM textscoperegistry.azurecr.io/opencv_base_image:ubuntu20.04

ENV PYTHONPATH="$PYTHONPATH:/workspace"

RUN apt-get install nano && \
    apt-get install -y git  && \
    apt-get install wget

RUN pip3 install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html

RUN pip3 install typing && \
    pip3 install pydantic[dotenv] && \
    pip3 install pydantic[email]

RUN pip3 install fastapi uvicorn

COPY . /workspace

WORKDIR /workspace/lovit
RUN python3 setup.py install && \
    rm -r /workspace/lovit

RUN pip3 install soynlp

WORKDIR /workspace
