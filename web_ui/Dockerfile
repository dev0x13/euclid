FROM python:3

ARG version

# 1. Parser backend

RUN apt-get update && \
    apt-get install -y apt-transport-https \
                       ca-certificates \
                       curl \
                       gnupg-agent \
                       software-properties-common && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu xenial stable" && \
    apt-get update && \
    apt-get install -y docker-ce docker-ce-cli containerd.io

# 2. Flask frontend

WORKDIR /app

ADD ./requirements.txt ./
ADD ./docker_entrypoint.sh ./
ADD ./tools/init_mongo_scheme.py ./

RUN pip install --no-cache-dir -r requirements.txt

ADD ./application ./

ENTRYPOINT ./docker_entrypoint.sh 
