FROM python:3.8-slim-buster

ARG BRANCH
ARG CONFIG_BRANCH

RUN mkdir /run/secrets/
RUN --mount=type=secret,id=CONFIG_REPOSITORY_KEY,dst=/run/secrets/CONFIG_REPOSITORY_KEY,required echo "$(cat /run/secrets/CONFIG_REPOSITORY_KEY)" && ls -l /run/secrets

RUN apt update
RUN apt install python3-pip git -y
RUN python3 -m pip install waitress
RUN python3 -m pip install --upgrade pip

RUN git clone --branch $BRANCH https://github.com/FAUSheppy/flask-json-dream-website /app
WORKDIR /app

RUN mkdir ~/.ssh/
RUN ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN --mount=type=secret,id=CONFIG_REPOSITORY \
    --mount=type=secret,id=CONFIG_REPOSITORY_KEY \
    eval `ssh-agent -s` && \
    echo "$(cat /run/secrets/CONFIG_REPOSITORY_KEY)" | ssh-add - && \
    git clone --branch ${CONFIG_BRANCH} $(cat /run/secrets/CONFIG_REPOSITORY) content

RUN ln -s content/config.py config_prod.py

RUN python3 -m pip install --no-cache-dir -r req.txt

HEALTHCHECK CMD --interval=5m --timeout=5s /usr/bin/curl http://localhost:5000/ || exit 1
EXPOSE 5000/tcp

RUN apt remove git -y
RUN apt autoremove -y

CMD waitress-serve --host 0.0.0.0 --port 5000 --call 'app:createApp'
