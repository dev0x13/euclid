FROM python:3

WORKDIR /env

ADD ./executor.py ./
ADD ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT python executor.py
