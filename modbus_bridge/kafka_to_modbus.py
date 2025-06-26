from kafka import KafkaConsumer
from ModbusBorunteClient import ModbusBorunteClient, ModbusBorunteError
from datetime import datetime

import json, time, os, logging, socket


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("ModbusBorunteClient")

# Variables de entorno con valores por defecto
PROCESS_ID = os.getenv("PROCESS_ID", "kafka_to_mode_bridge")
BORUNTE_IP = os.getenv("BORUNTE_IP", "192.168.18.89")
TARGET_ID = os.getenv("TARGET_ID", "borunte_test_01")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC_COMMANDS", "robot.commands")
KAFKA_TOPIC_STATUS = os.getenv("KAFKA_TOPIC_STATUS", "robot.status")
KAFKA_TOPIC_RESPONSES = os.getenv("KAFKA_TOPIC_RESPONSES", "robot.responses")
KAFKA_RETRY = int(os.getenv("KAFKA_RETRY", 30))
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "modbus_bridge_group")
STATUS_RATE = int(os.getenv("STATUS_RATE", 5))


def crear_modbus_robot():
    robot = ModbusBorunteClient(host=BORUNTE_IP, name_id=TARGET_ID)
    if robot.connect():
        logger.info(f"Conectado a robot BORUNTE en {BORUNTE_IP}")
        return robot
    logger.warning("No se pudo conectar al robot.")
    return None

def crear_kafka_consumer():
    consumer = KafkaConsumer(
        KAFKA_TOPIC_COMMANDS,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id=GROUP_ID,
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )
    return consumer

def wait_for_kafka(broker="localhost:9092", retries=30, timeout=90):
    host, port = broker.split(":")
    print(f"🔍 Esperando que Kafka esté disponible en {host}:{port}...")
    for attempt in range(retries):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                print("✅ Puerto Kafka activo, iniciando productor")
                return
        except (socket.timeout, ConnectionRefusedError):
            print(f"⏳ Kafka no responde (intento {attempt+1}/{retries})...")
            time.sleep(3)
    raise RuntimeError("❌ Kafka no se conectó tras múltiples intentos")


def main(consumer=None):
    logger.info("🟢 Lectura de comandos iniciada.")
    error_count = 0
    for msg in consumer:
        key = msg.key.decode() if msg.key else None
        data = msg.value

        if key != TARGET_ID:
            continue

        order_id = data["order_id"]
        method_name = data["name"]
        params = data.get("params", [])
        print(f"📦 Orden recibida: {order_id} - {method_name} - {params}")
        robot = crear_modbus_robot()
        robot.connect()

        if method_name.startswith('_') and hasattr(robot, method_name):
            logger.warning(f"⛔ Método no permitido o inexistente: {method_name}")
            continue
        
        method = getattr(robot, method_name)    
        if "button" in method_name:
            logger.info(f"🔧 Ejecutando método: {method_name}")
            result = method()
            logger.info(f"🔧 Resultado: {result}")
            continue
        if "process" in method_name:
            logger.info(f"🔧 Ejecutando método: {method_name}")
            result = method(*params)
            logger.info(f"🔧 Resultado: {result}")
            continue

if __name__ == "__main__":
    wait_for_kafka(broker=KAFKA_BROKER, retries=KAFKA_RETRY)

    while True:
        try:
            consumer = crear_kafka_consumer()
            main(consumer)
        except Exception as e:
            logger.error(f"🔴 Error en el bucle principal: {e}")


        