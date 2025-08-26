FROM python:3.10-slim

#ENV PYTHONUNBUFFERED=1
ENV TINI_VERSION=v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# COPY config.yaml kafka_to_opc.py opc_to_kafka.py OpcClientPLC.py ./
COPY entrypoint.sh ./

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/tini","--", "/app/entrypoint.sh"]