from kafka import KafkaProducer
from ModbusBorunteClient import ModbusBorunteClient, ModbusBorunteError
from datetime import datetime

import json, time, os, logging, socket, signal


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("ModbusBorunteClient")

# Variables de entorno con valores por defecto
PROCESS_ID = os.getenv("PROCESS_ID", "modbus_to_kafka_bridge")
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
        logger.info(f"🟢 Conectado a robot BORUNTE en {BORUNTE_IP}: {TARGET_ID}")
        return robot
    logger.warning("🟡 No se pudo conectar al robot.")
    return None

def crear_kafka_producer():
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda m: json.dumps(m).encode('utf-8')
    )
    logger.info(f"🟢 Productor Kafka creado {KAFKA_BROKER}")
    return producer

def wait_for_kafka(broker="localhost:9092", retries=30, timeout=2):
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


def main(robot=None, producer=None):
    logger.info("🟢 Lectura de status iniciado.")
    error_count = 0
    while error_count < 3:
        try:
            data = robot.read_borunte_data_all()
            payload = {
                "target_id": TARGET_ID,
                "ip": BORUNTE_IP,
                "online": True,
                "status": data,
                "timestamp": datetime.now().isoformat() + "Z"
            }
            producer.send(KAFKA_TOPIC_STATUS, key=TARGET_ID.encode('utf-8'), value=payload)
            logger.info("📡 Status enviado al broker Kafka.")
            time.sleep(STATUS_RATE)
        except ModbusBorunteError as e:
            logger.error(f"🔴 Error de lectura de status: {e}")
        except Exception as e:
            logger.error(f"🔴 Error en hilo de status: {e}") 
            error_count += 1
        
    logger.info("🔴 Lectura de status detenido.")

if __name__ == "__main__": 
    wait_for_kafka(broker=KAFKA_BROKER, retries=KAFKA_RETRY)

    while True:
        try:
            robot = crear_modbus_robot()
            if robot is None:
                logger.warning(f"❌ Robot en {BORUNTE_IP}: {TARGET_ID} no disponible RECONECTANDO...")
                time.sleep(5)
                continue
            producer = crear_kafka_producer()
            main(robot, producer)
        except Exception as e:
            logger.error(f"🔴 Error en el bucle principal: {e}")