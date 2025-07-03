FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY config.yml kafka_to_opc.py opc_to_kafka.py entreypoint.sh requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

#CMD ["python", "kafka_opc_bridge.py"]
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]