FROM python:3

ARG version

WORKDIR /app

ADD ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

ADD ./app/ ./

ENTRYPOINT python app.py runserver

