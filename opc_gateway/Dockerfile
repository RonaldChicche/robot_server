FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY config.yaml kafka_to_opc.py opc_to_kafka.py OpcClientPLC.py entrypoint.sh ./

#CMD ["python", "kafka_opc_bridge.py"]
RUN chmod +x /app/entrypoint.sh
#ENTRYPOINT ["/app/entrypoint.sh"]
ENTRYPOINT ["sh", "/app/entrypoint.sh"]