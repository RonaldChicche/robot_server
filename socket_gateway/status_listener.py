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
STATUS_INTERVAL=1    #os.getenv("STATUS_INTERVAL", 5)\

KAFKA_TOPIC_STATUS = os.getenv("KAFKA_TOPIC_STATUS", "robot.status")
KAFKA_TOPIC_RESPONSE = os.getenv("KAFKA_TOPIC_RESPONSE", "robot.responses")

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
        keys = load_keys(path="common/redis_keys.yaml")  # puedes usarlo luego si deseas aplicar filtros
        redis_client = create_redis_client(REDIS_HOST, REDIS_PORT)
        kafka_producer = create_kafka_producer(KAFKA_BROKER)
    except Exception as e:
        logger.error(f"❌ Error inesperado al iniciar: {e}", exc_info=True)
        graceful_shutdown()

    logger.info("📡 Iniciando status_listener...")
    # variables para comparar
    last_status_time = {
        "01": 0,
        "02": 0
    }
    last_raw_results = {
        "01": None,
        "02": None
    }

    time.sleep(5)

    while True:
        current_time = time.time()
        for robot_id in ROBOT_IDS:
            try:
                # result data
                result_key = keys["status_listener"]["redis_result_template"].format(id=robot_id)
                raw_data = redis_client.get(result_key)
                if raw_data:
                    raw_result = json.loads(raw_data)
                    if last_raw_results.get(robot_id) != raw_result:
                        kafka_producer.send(KAFKA_TOPIC_RESPONSE, value=raw_result)
                        last_raw_results[robot_id] = raw_result  
                
                 # status data
                if current_time - last_status_time[robot_id] >= float(STATUS_INTERVAL):
                    sensor_key = keys["status_listener"]["redis_sensor_template"].format(id=robot_id)
                    connection_key = keys["status_listener"]["redis_robot_connected"].format(id=robot_id)
                    process_status_key = keys["process_coordinator"]["process_state"].format(id=robot_id)
                    last_status_time[robot_id] = current_time
                    raw_data = redis_client.get(sensor_key)
                    if raw_data:
                        raw_status = json.loads(raw_data)  
                        # Error de desconneccion 
                        if redis_client.get(connection_key) is None:
                            logger.error(f"⚠️ Robot {robot_id} desconectado")
                            raw_status["status"]["status"]["alarm_code"] = [9001]
                            raw_data = redis_client.get(sensor_key)    
                        # Logica de status de feedback
                        process_status = redis_client.get(process_status_key) 
                        raw_status.setdefault("process_status", {})
                        if process_status is not None:
                            bit_green = process_status == "Running"
                            bit_yellow = process_status == "Paused"
                            bit_red = process_status == "Stopped"

                            # En todos los demás casos, los bits están apagados (incluye Vacio y Terminado)
                            if process_status not in ["Running", "Paused", "Stopped"]:
                                bit_green = bit_yellow = bit_red = False

                            raw_status["process_status"]["state"] = process_status
                            raw_status["process_status"]["bit_green"] = bit_green
                            raw_status["process_status"]["bit_yellow"] = bit_yellow
                            raw_status["process_status"]["bit_red"] = bit_red
                        else:
                            raw_status["process_status"] = {"bit_green": False, "bit_yellow": False, "bit_red": False}
                        
                        kafka_producer.send(KAFKA_TOPIC_STATUS, value=raw_status)                
                    else:
                        logger.warning(f"⚠️ No se encontró status para robot {robot_id}")                    
                            
                    raw_status = None
            
            except (json.JSONDecodeError, KeyError, TypeError) as known_error:
                logger.error(f"⚠️ Datos mal formados para {robot_id}: {known_error}", exc_info=True)
            except Exception as fatal_error:
                logger.error(f"❌ Error inesperado con {robot_id}: {fatal_error}", exc_info=True)
                graceful_shutdown()



if __name__ == "__main__":
    main()