FROM nginx:latest

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ARG NGINX_FILE_DEFAULT
ARG NGINX_FILE_NGINX

RUN apt-get -qq update \
    && apt-get -y -qq install \
        sudo \
        locales \
        openssh-server \
    && locale-gen ko_KR.UTF-8

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y -qq install \
    python3-pip \
    python3-venv \
    tzdata \
    vim

RUN sed -i 's/#Port 22/Port 22/g' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config


RUN echo "root:lomin0505!" | chpasswd

COPY ./${NGINX_FILE_DEFAULT} /etc/nginx/conf.d/default.conf
COPY ./${NGINX_FILE_NGINX} /etc/nginx/nginx.conf

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]