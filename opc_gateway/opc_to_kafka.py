from kafka import KafkaProducer
from OpcClientPLC import OpcClient  

import os, time, json, logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("OpctoKafka")

# === 🔧 Cargar configuración desde entorno ===
PROCESS_ID = os.getenv("PROCESS_ID", "modbus_to_kafka_bridge")
#OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://192.168.18.89:62640/IntegrationObjects/ServerSimulator")
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC_COMMANDS", "robot.commands")


def crear_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )


def main():
    producer = crear_kafka_producer()
    logger.info(f"🔗 Conectando a {OPC_ENDPOINT} ...")
    opc = OpcClient(OPC_ENDPOINT, kafka_producer=producer, kafka_topic=KAFKA_TOPIC_COMMANDS)
    opc.subscribe_bits()

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
            #response = opc.read_all_inputs()
            print("Estado de las entradas ok")
            time.sleep(30)
        except KeyboardInterrupt:
            graceful_shutdown()
            logger.info("🔴 Lectura de comandos detenido.")
            return
        except Exception as e:
            logger.error(f"🔴 Error en hilo de heart beat: {e}")
            error_count += 1
        
        if error_count >= 3:
            graceful_shutdown()
            logger.info("🔴 Lectura de comandos detenido.")
            return
        

if __name__ == "__main__":
    main()
            
