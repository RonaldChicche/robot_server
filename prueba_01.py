#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer

# Configuración del broker Kafka
KAFKA_BROKER = "190.168.10.102:9092"
TOPIC = "robot.commands"

# Mensaje base reproducible
address = 811
value = -1196266
permanent = 0

# Construcción del mensaje
payload = {
    "order_id": f"ORD_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}",
    "type": "method",
    "name": "write_data_single",
    "params": {
        "addres": address,
        "value": value,
        "permanent": permanent
    },
    "timestamp": datetime.now().strftime('%Y%m%dT%H%M%SZ')
}

# Inicializar productor Kafka
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8")
)

# Enviar mensaje
producer.send(TOPIC, key=payload["order_id"], value=payload)
producer.flush()

print(f"✅ Mensaje enviado a '{TOPIC}':\n{json.dumps(payload, indent=2)}")
