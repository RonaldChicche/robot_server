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
BORUNTE_IP = os.getenv("BORUNTE_IP", "192.168.100.21")
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


def main():
    consumer = crear_kafka_consumer()
    robot = crear_modbus_robot()
    robot.connect()
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
        try:           
            logger.info(f"🔧 Ejecutando método: {method_name}")
            if "start_button" == method_name:  
                result = robot.start_button()
                logger.info(f"🔧 Resultado: {result}")
            elif "pause_button" == method_name:
                result = robot.pause_button()
                logger.info(f"🔧 Resultado: {result}")
            elif "stop_button" == method_name:
                result = robot.stop_button()
                logger.info(f"🔧 Resultado: {result}")
            elif "clear_alarm_button" == method_name:
                result = robot.clear_alarm_button()
                logger.info(f"🔧 Resultado: {result}")
            elif "clear_alarm_and_resumen_button" == method_name:
                result = robot.clear_alarm_and_resume_button()
                logger.info(f"🔧 Resultado: {result}")
            elif "force_stop_button" == method_name:
                result = robot.force_stop_button()
                logger.info(f"🔧 Resultado: {result}")
            elif "proceso" in method_name:
                result = robot.proceso_01(params)
                logger.info(f"🔧 Resultado: {result}")
            else:
                logger.warning(f"⛔ Método no permitido o inexistente: {method_name}")
        except Exception as e:
            logger.error(f"🔴 Error en hilo de comandos: {e}", exc_info=True)


if __name__ == "__main__":
    wait_for_kafka(broker=KAFKA_BROKER, retries=KAFKA_RETRY)
    main()


        