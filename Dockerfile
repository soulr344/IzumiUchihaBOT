FROM python:3.9-slim

WORKDIR /tgbot
COPY . /tgbot
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update -y
RUN apt-get install -y iputils-ping

CMD ["python", "-m", "tg_bot"]
