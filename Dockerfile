FROM ubuntu:latest
MAINTAINER Joemar Taganna

WORKDIR /home
RUN apt-get update
RUN apt-get install git
RUN git clone https://github.com/cognitronz/neuraltalk
