from common.utils import create_kafka_producer, load_keys, create_redis_client

import os, json, logging, signal, sys, time


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("StatusListener")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC_STATUS = os.getenv("KAFKA_TOPIC_STATUS", "robot.status")
STATUS_INTERVAL=os.getenv("STATUS_INTERVAL", 5)

ROBOT_IDS = ["01", "02"]


redis_client = None
kafka_producer = None

def graceful_shutdown(sig=None, frame=None):
    logger.info("🛑 Apagando status_listener...")
    try:
        if kafka_producer:
            kafka_producer.close()
            logger.info("✅ Kafka cerrado")
        if redis_client:
            redis_client.close()
            logger.info("✅ Redis cerrado")
    except Exception as e:
        logger.error(f"⚠️ Error al cerrar conexiones: {e}", exc_info=True)
    sys.exit(0)

def format_status(raw_status, robot_id):
    return {
        "robot_id": robot_id,
        "online": True,
        "status": raw_status,
    }

def main():
    global redis_client, kafka_producer
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    try:
        load_keys('common/redis_keys.yaml')  # puedes usarlo luego si deseas aplicar filtros
        redis_client = create_redis_client(REDIS_HOST, REDIS_PORT)
        kafka_producer = create_kafka_producer(KAFKA_BROKER)
    except Exception as e:
        logger.error(f"❌ Error inesperado al iniciar: {e}", exc_info=True)
        graceful_shutdown()

    logger.info("📡 Iniciando status_listener...")
    time.sleep(5)

    while True:
        for robot_id in ROBOT_IDS:
            key = f"robot:{robot_id}:raw_response"
            try:
                raw_data = redis_client.get(key)
                if raw_data:
                    raw_status = json.loads(raw_data)
                    kafka_producer.send(KAFKA_TOPIC_STATUS, value=raw_status)
                    #print(f"✅ Enviado status de robot {robot_id} a Kafka")
                else:
                    logger.warning(f"⚠️ No se encontró status para robot {robot_id}")
            
            except (json.JSONDecodeError, KeyError, TypeError) as known_error:
                logger.error(f"⚠️ Status mal formado para {robot_id}: {known_error}")
            except Exception as fatal_error:
                logger.error(f"❌ Error inesperado con {robot_id}: {fatal_error}", exc_info=True)
                graceful_shutdown()

        time.sleep(int(STATUS_INTERVAL))


if __name__ == "__main__":
    main()