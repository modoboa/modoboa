FROM python:3.6-alpine

MAINTAINER Antoine Nguyen <tonio@ngyn.org>

RUN apk add --update openssl python3-dev libffi-dev gcc musl-dev libxml2-dev libxslt-dev \
    libressl-dev jpeg-dev \
    && rm -rf /var/cache/apk/*

WORKDIR /tmp
COPY requirements.txt /tmp
COPY test-requirements.txt /tmp
RUN pip install -r requirements.txt -r test-requirements.txt

RUN mkdir /code
WORKDIR /code
