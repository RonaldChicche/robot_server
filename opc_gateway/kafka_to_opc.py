import os
import time
import json
import signal
from kafka import KafkaProducer
from OpcClientPLC import OpcClient  


OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://192.168.18.89:62640/IntegrationObjects/ServerSimulator")
KAFKA_IP = os.getenv("KAFKA_IP", "127.0.0.1")
KAFKA_PORT = os.getenv("KAFKA_PORT", 9092)
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC_COMMANDS", "robot.to_robots")


def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=f"{KAFKA_IP}:{KAFKA_PORT}",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",  
        retries=5
    )


def main():
    producer = get_kafka_producer()
    opc = None

    def graceful_shutdown(signum, frame):
        print("🛑 Finalizando...")
        if opc:
            opc.disconnect()
        producer.flush()
        producer.close()
        exit(0)


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
