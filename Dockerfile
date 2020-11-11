FROM python=3.6.9

WORKDIR ./code

COPY src/ .

CMD [ "python3", "./server.py" ]


