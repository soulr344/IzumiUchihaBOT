FROM python:3.6.9
WORKDIR /tgbot
ADD . /tgbot
RUN pip3 install -r requirements.txt
EXPOSE 80
EXPOSE 8080
EXPOSE 5432
EXPOSE 443
CMD python3.6 -m tg_bot
