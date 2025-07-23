from kafka import KafkaProducer
from OpcClientPLC import OpcClient
import os, time, json, logging, signal, sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)


logging.getLogger("opcua.client.ua_client").setLevel(logging.WARNING)
logging.getLogger("opcua.uaprotocol").setLevel(logging.WARNING)

logger = logging.getLogger("OpctoKafka")

PROCESS_ID = os.getenv("PROCESS_ID", "opc_to_kafka_bridge")
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC_COMMANDS", "robot.commands")

producer = None
opc = None
prev_state = {}  # Para detectar flancos positivos
def crear_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

def graceful_shutdown(sig=None, frame=None):
    logger.info("🛑 Finalizando proceso OPC ➜ Kafka...")
    try:
        if opc:
            opc.disconnect()
            logger.info("✅ Cliente OPC desconectado")
        if producer:
            producer.flush()
            producer.close()
            logger.info("✅ Kafka producer cerrado")
    except Exception as e:
        logger.error(f"⚠️ Error durante shutdown: {e}", exc_info=True)
    sys.exit(0)

def main():
    global producer, opc, prev_state
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    try:
        producer = crear_kafka_producer()
        logger.info(f"🔗 Conectando a {OPC_ENDPOINT} ...")
        opc = OpcClient(OPC_ENDPOINT, kafka_producer=producer, kafka_topic=KAFKA_TOPIC_COMMANDS)
        logger.info("🟢 Iniciando ciclo de lectura")
    except Exception as e:
        logger.error(f"❌ Error al inicializar OPC o Kafka: {e}", exc_info=True)
        graceful_shutdown()

    error_count = 0

    while error_count < 3:
        try:
            opc.read_all_inputs()
            #logger.info(f"📊 Parámetros actuales: {opc.values}")
            time.sleep(0.1)

        except KeyboardInterrupt:
            graceful_shutdown()
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error en ciclo principal: {e}", exc_info=True)
            time.sleep(2)

    graceful_shutdown()

if __name__ == "__main__":
    main()
