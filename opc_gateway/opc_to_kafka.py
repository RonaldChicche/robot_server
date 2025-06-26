import os
import time
import json
import socket
import signal
import logging
from datetime import datetime
from kafka import KafkaProducer
from OpcClientPLC import OpcClient  


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("OpcPlcClient")

# === 🔧 Cargar configuración desde entorno ===
PROCESS_ID = os.getenv("PROCESS_ID", "modbus_to_kafka_bridge")
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://192.168.18.89:62640/IntegrationObjects/ServerSimulator")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC_COMMANDS", "robot.commands")
KAFKA_TOPIC_STATUS = os.getenv("KAFKA_TOPIC_STATUS", "robot.status")
KAFKA_GRUOP_ID = os.getenv("KAFKA_GRUOP_ID", "opc_to_kafka_group")
KAFKA_RETRY = int(os.getenv("KAFKA_RETRY", 30))

# === 🔌 Kafka Producer ===
def crear_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

def wait_for_kafka_socket(broker="localhost:9092", retries=30, timeout=2):
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


def main(opc=None, producer=None):
    logger.info("🟢 Lectura de comandos iniciado ...")

    def graceful_shutdown():
        print("🛑 Finalizando...")
        if opc:
            opc.disconnect()
        producer.flush()
        producer.close()
        exit(0)

    error_count = 0
    while error_count < 3:
        try:
            # opc heart beat
            response = opc.read_all_inputs()
            print("Estado de las entradas:", response)
            time.sleep(3)
        except Exception as e:
            logger.error(f"🔴 Error en hilo de heart beat: {e}")
            error_count += 1
    graceful_shutdown()
    logger.info("🔴 Lectura de comandos detenido.")

if __name__ == "__main__":
    wait_for_kafka_socket(broker=KAFKA_BROKER, retries=KAFKA_RETRY)
    producer = None
    while True:
        try:
            producer = crear_kafka_producer()
            logger.info(f"🔗 Conectando a {OPC_ENDPOINT} ...")
            opc = OpcClient(OPC_ENDPOINT, kafka_producer=producer, kafka_topic=KAFKA_TOPIC_COMMANDS)
            opc.subscribe_bits()
            main(opc=opc, producer=producer)
        except Exception as e:
            logger.error("🔴 Error en el bucle principal: {}".format(e), exc_info=True)
            time.sleep(5)
            
