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
    "robot_id": "borunte_test_01",
    "type": "method",
    "name": "write_output",
    "args": ["y13", 0],
    "kwargs": {},
    "timestamp": datetime.now().isoformat() + "Z"
}

# Envía el mensaje con robot_id como key
future = producer.send(
    TOPIC,
    value=mensaje,
    key=mensaje["robot_id"]
)

# Espera confirmación de envío
try:
    result = future.get(timeout=5)
    print(f"✅ Mensaje enviado: {result}")
except Exception as e:
    print(f"❌ Error al enviar mensaje: {e}")

producer.close()
