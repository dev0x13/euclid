FROM python:3

WORKDIR /env

ADD ./executor.py ./
ADD ./validator.py ./
ADD ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
