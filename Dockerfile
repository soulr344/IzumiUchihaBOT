FROM python:3.10
RUN apt-get update
RUN apt-get install -y python3-dev git flac \
                       iputils-ping net-tools
WORKDIR /root/HyperUBot
COPY ./ ./
RUN python3 -m pip install --upgrade pip setuptools
RUN python3 -m pip install -r requirements.txt
CMD ["python3", "-m", "tg_bot"]
