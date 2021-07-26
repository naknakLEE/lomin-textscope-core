FROM textscoperegistry.azurecr.io/opencv_base_image:ubuntu18.04

ENV PYTHONPATH="$PYTHONPATH:/workspace"

RUN apt-get install nano && \
    apt-get install -y git  && \
    apt-get install wget

# RUN apt-get install libgl1-mesa-glx
# RUN apt-get install libgtk2.0-dev


RUN pip3 install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html

RUN pip3 install typing && \
    pip3 install pydantic[dotenv] && \
    pip3 install pydantic[email]

RUN pip3 install fastapi uvicorn

RUN pip3 install tifffile && \
    pip3 install pdf2image && \
    pip3 install scikit-image

COPY . /workspace

WORKDIR /workspace/lovit
RUN python3 setup.py install && \
    rm -r /workspace/lovit

RUN pip3 install soynlp && \
    pip3 install loguru && \
    pip3 install httpx && \
    pip3 install Shapely && \
    pip3 install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/lts/1.8/torch_lts.html

WORKDIR /workspace
