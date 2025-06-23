FROM python:3.10-slim

WORKDIR /app

COPY kafka_modbus_bridge.py ModbusBorunteClient.py requirements.txt ./
#COPY config ./config

# instala dependencias
RUN pip install -r requirements.txt

CMD ["python", "kafka_modbus_bridge.py"]
