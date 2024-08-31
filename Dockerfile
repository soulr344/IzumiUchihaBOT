FROM python:3.9-slim

WORKDIR /tgbot
COPY . /tgbot
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "tg_bot"]
