import os
import time
import json
import socket
import signal
from datetime import datetime
from kafka import KafkaProducer
from OpcClientPLC import OpcClient  # Tu clase ya con SubHandler y lógica

# === 🔧 Cargar configuración desde entorno ===
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://192.168.18.89:62640/IntegrationObjects/ServerSimulator")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC_COMMANDS", "robot.to_robots")

# === 🔌 Kafka Producer ===
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",  # wait for full commit
        retries=5
    )

def wait_for_kafka_socket(host="localhost", port=9092, timeout=1, retries=30):
    print(f"🔍 Esperando que Kafka esté disponible en {host}:{port}...")
    for attempt in range(retries):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                print("✅ Puerto Kafka activo, iniciando productor")
                return
        except (socket.timeout, ConnectionRefusedError):
            print(f"⏳ Kafka no responde (intento {attempt+1}/{retries})...")
            time.sleep(2)
    raise RuntimeError("❌ Kafka no se conectó tras múltiples intentos")

# === 🧠 Main Loop con reconexión y manejo de errores ===
def main():
    host, port = KAFKA_BROKER.split(":")
    wait_for_kafka_socket(host, int(port))

    producer = get_kafka_producer()
    opc = None

    def graceful_shutdown(signum, frame):
        print("🛑 Finalizando...")
        if opc:
            opc.disconnect()
        producer.flush()
        producer.close()
        exit(0)

    # Capturar Ctrl+C
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    while True:
        try:
            print(f"🔗 Conectando a {OPC_ENDPOINT} ...")
            opc = OpcClient(OPC_ENDPOINT, kafka_producer=producer, kafka_topic=KAFKA_TOPIC_COMMANDS)
            opc.subscribe_bits()
            print("🟢 Subscripciones activas. Esperando cambios...")
            while True:
                time.sleep(1)

        except Exception as e:
            print(f"⚠️ Error en conexión o ejecución: {e}")
            time.sleep(5)
            print("🔁 Reintentando conexión OPC...")

if __name__ == "__main__":
    main()
