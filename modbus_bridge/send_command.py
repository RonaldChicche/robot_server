from kafka import KafkaProducer
import json
from datetime import datetime

# Configura los parámetros
KAFKA_BROKER = "localhost:9092"  # Cambia si estás usando docker o red externa
TOPIC = "robot.commands"

# Crea el productor
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# Mensaje de comando
mensaje = {
    "order_id": "ORD_20230626123456_borunte__test_01",
    "target_id": "borunte_test_01",
    "type": "method",
    "name": "start_button",
    "params": ["y13", 0],
    "kwargs": {},
    "timestamp": datetime.now().isoformat() + "Z"
}

# Envía el mensaje con robot_id como key
future = producer.send(
    TOPIC,
    value=mensaje,
    key=mensaje["target_id"].encode("utf-8")
)

# Espera confirmación de envío
try:
    result = future.get(timeout=5)
    print(f"✅ Mensaje enviado: {result}")
except Exception as e:
    print(f"❌ Error al enviar mensaje: {e}")

producer.close()
