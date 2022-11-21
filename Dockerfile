# Copyright 2021-2022 nunopenim @github
# Copyright 2021-2022 prototype74 @github
# Copyright 2022 soulr344 @github
#
# Licensed under the PEL (Penim Enterprises License), v1.0
#
# You may not use this file or any of the content within it, unless in
# compliance with the PE License

FROM python:3.10
RUN apt-get update
RUN apt-get install -y python3-dev git flac \
                       iputils-ping net-tools
WORKDIR /root/IzumiUchihaBOT
COPY ./ ./
RUN python3 -m pip install --upgrade pip setuptools
RUN python3 -m pip install -r requirements.txt
CMD ["python3", "-m", "tg_bot"]
