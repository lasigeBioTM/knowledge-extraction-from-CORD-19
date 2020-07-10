FROM ubuntu:18.04


RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip \
  && apt-get install -y \
    ssh \
    sqlite3 \
    libsqlite3-dev \
    git \
    mysql-server \
    && apt-get autoremove \
    && apt-get clean


COPY requirements.txt ./
RUN pip3 install -r requirements.txt

RUN mkdir /data
VOLUME /data

RUN mkdir /covid_rec_sys

VOLUME /covid_rec_sys





