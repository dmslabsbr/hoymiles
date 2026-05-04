ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.14-alpine3.23
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8

WORKDIR /app

COPY pyproject.toml setup.cfg setup.py README.md LICENSE.txt /app/
COPY src /app/src
RUN python -m pip install --upgrade pip \
    && pip3 install --no-cache-dir .

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
