FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY kafka_to_modbus.py modbus_to_kafka.py ModbusBorunteClient.py requirements.txt entrypoint.sh ./

RUN pip install -r requirements.txt

#CMD ["python", "kafka_modbus_bridge.py"]
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]