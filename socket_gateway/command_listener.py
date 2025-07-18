from common.utils import create_kafka_consumer, create_redis_client, load_keys
import os, json, logging, signal, sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("CommandListener")


KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC_COMMANDS", "robot.commands")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "socket_gateway_group")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

DEFAULT_ROBOT_IDS = ["01", "02"]


redis_client = None
kafka_consumer = None


def graceful_shutdown(sig=None, frame=None):
    logger.info("🛑 Apagando proceso por error o señal externa...")
    try:
        if kafka_consumer:
            kafka_consumer.close()
            logger.info("✅ Kafka cerrado")
        if redis_client:
            redis_client.close()
            logger.info("✅ Redis cerrado")
    except Exception as e:
        logger.error(f"⚠️ Error al cerrar conexiones: {e}")
    sys.exit(1)


def main():
    global redis_client, kafka_consumer
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    # Connection --------------------------------------------------------------------------
    try:
        keys = load_keys(path="common/redis_keys.yaml")
        redis_client = create_redis_client(REDIS_HOST, REDIS_PORT)
        kafka_consumer = create_kafka_consumer(KAFKA_TOPIC_COMMANDS, KAFKA_BROKER, KAFKA_GROUP_ID)
    except Exception as e:
        logger.error(f"❌ Error inesperado al iniciar: {e}", exc_info=True)
        graceful_shutdown()

    logger.info("📡 Listening for incoming commands...")

    for message in kafka_consumer:
        data = message.value
        logger.info(f"📥 Command received: {data}")
        
        # {'order_id': 'ORD_20250707T202825Z_borunte', 'type': 'method', 'name': 'start_button', 'params': {}, 'timestamp': '20250707T202825Z'}
        # {'order_id': 'ORD_20250707T202743Z_borunte', 'type': 'proceso', 'name': 'send_data', 'params': {'ancho_caja': 150.0, 'long_barra': '3658', 'ancho_barra': 101.6, 'espesor': 6.35, 'peso': 21.0, 'cantidad': 4, 'no_carro': 1}, 'timestamp': '20250707T202743Z'}
        try:
            cmd_type = data.get("type")
            if cmd_type in ["method"]:
                target_ids = [data.get("robot_id")] if data.get("robot_id") else DEFAULT_ROBOT_IDS
                for robot_id in target_ids:
                    redis_key = keys["command_listener"]["robot_cmd_template"].format(id=robot_id)
                    redis_client.set(redis_key, json.dumps(data), ex=2)
                    logger.info(f"📤 Comando '{cmd_type}' almacenado en Redis: {redis_key}")

            elif cmd_type == "proceso":
                redis_key = keys["command_listener"]["robot_process_template"]
                redis_client.set(redis_key, json.dumps(data))    # expira?
                logger.info(f"📦 Proceso parameters stored in Redis: {redis_key}")
                
            else:
                logger.warning(f"⚠️ Invalid command type ... Skipping - {cmd_type}")
        
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as known_error:
            logger.error(f"⚠️ Error procesando mensaje inválido: {known_error}", exc_info=True)
        except Exception as fatal_error:
            logger.error(f"💥 Error inesperado. Cerrando...: {fatal_error}", exc_info=True)
            graceful_shutdown()


if __name__ == "__main__":    
    main()