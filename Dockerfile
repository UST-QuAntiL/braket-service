FROM python:3.7-slim

MAINTAINER Marie Salm "marie.salm@iaas.uni-stuttgart.de"

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN sudo ./aws/install

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN apt-get update
RUN apt-get install -y gcc python3-dev
RUN pip install -r requirements.txt
COPY . /app

EXPOSE 5019/tcp

ENV FLASK_APP=braket-service.py
ENV FLASK_ENV=development
ENV FLASK_DEBUG=0
RUN echo "python -m flask db upgrade" > /app/startup.sh
RUN echo "gunicorn braket-service:app -b 0.0.0.0:5019 -w 4 --timeout 500 --log-level info" >> /app/startup.sh
CMD [ "sh", "/app/startup.sh" ]
