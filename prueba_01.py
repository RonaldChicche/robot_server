from kafka import KafkaProducer
import json
from datetime import datetime

# Configura los parámetros
KAFKA_BROKER = "192.168.101.10:9092"  # Cambia si estás usando docker o red externa
TOPIC = "robot.commands"
CMD = "send_data"
#CMD = "start"

# Crea el productor
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

timestamp = datetime.now().isoformat()
# Mensaje de comando
data_msg = {
    "order_id": f"ORD_{timestamp}_borunte_test_01",
    "robot_id" : "01",
    "type": "method",
    "name": "proceso_01",
    "params": {
        "pick": [1591.237, 1033.584, 429.415, -179.725, -0.057, -148.847],
        "put": [2686.084, 1033.584, 306.190, 179.728, -0.093, -148.850],
        "cantidad": 5,
        "dx": 0,
        "dy": 0,
        "altura": 5,
        "velocidad": 1000
    },
    "timestamp": timestamp + "Z"
}

start_msg = {
    "order_id": f"ORD_{timestamp}_borunte_test_01",
    "robot_id" : "01",
    "type": "method",
    "name": "start_button",
    "params": {},
    "timestamp": timestamp + "Z"
}

# Envía el mensaje con robot_id como key
if CMD == "send_data":
    mensaje = data_msg
else: 
    mensaje = start_msg

future = producer.send(
    TOPIC,
    value=mensaje
)

# Espera confirmación de envío
try:
    result = future.get(timeout=5)
    print(f"✅ Mensaje enviado: {result}")
except Exception as e:
    print(f"❌ Error al enviar mensaje: {e}")

producer.close()


#  450.667