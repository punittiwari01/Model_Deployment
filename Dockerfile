# This file was generated using recommend version 0.1.1.
FROM ubuntu:17.10

EXPOSE 8080

# Replace shell with bash so we can source files
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Update the apt-get and installs curl
RUN apt-get update \
  && apt-get install -y curl

# Installs node.js, python, pip and setup tools
RUN apt-get install -y \
    python3 \
    python3-pip \
    python3-setuptools \
    build-essential \
    libzmq3-dev

# Upgrade pip
RUN pip3 install --upgrade pip


RUN pip3 install click \
                 tornado \
                 requests \
                 wikipedia

COPY . .

ENTRYPOINT ["python3", "launch.py"]
