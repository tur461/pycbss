FROM python:3.6
ADD ./server.py /
ADD ./CommonProperties.py /
RUN mkdir -p /logs
RUN pip3 install autobahn twisted
EXPOSE 9090
CMD [ "python3", "./server.py" ]
