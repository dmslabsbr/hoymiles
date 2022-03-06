ARG BUILD_FROM=homeassistant/amd64-base-python:3.7-alpine3.12
FROM $BUILD_FROM

ENV LANG C.UTF-8

#https://github.com/home-assistant/docker-base
# erro em amd64-base-python:3.9-alpine3.12

# Install requirements for add-on
#RUN apk add --no-cache python3 py3-pip 

RUN pip3 install paho-mqtt
RUN pip3 install requests
RUN pip3 install flask

# Python 3 HTTP Server serves the current working dir
# So let's set it to our add-on persistent data directory.
WORKDIR /data

# other copy
COPY *.json /
COPY *.py /
COPY secrets.ini /data
COPY secrets.ini /
#COPY *.html /

COPY templates /

# Copy data for add-on
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]