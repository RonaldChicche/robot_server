from common.utils import create_kafka_producer, load_keys, create_redis_client

import os, json, logging, signal, sys, time, copy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("StatusListener")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
STATUS_INTERVAL = 1  # segundos entre lecturas

KAFKA_TOPIC_STATUS = os.getenv("KAFKA_TOPIC_STATUS", "robot.status")
KAFKA_TOPIC_RESPONSE = os.getenv("KAFKA_TOPIC_RESPONSE", "robot.responses")

ROBOT_IDS = ["01"]

redis_client = None
kafka_producer = None

# Estado global de timers por robot
timers = {
    robot_id: {
        "total_start": None,
        "total_end": None,
        "bars": [],          # lista de dicts {"start": float, "end": float, "duration": float}
        "current_bar": None, # dict o None
        "running": False,
        "complete": False,
        "prev_y42": False,   # para detectar flanco de subida
        "reported": False,   # para no repetir reporte final
    }
    for robot_id in ROBOT_IDS
}

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

def update_timers(robot_id, raw_status, process_status):
    global timers
    outputs = raw_status.get("status", {}).get("outputs", {}).get("y", {})

    # Lectura de señales
    y30 = outputs.get("y30", False)  # inicio real
    y32 = outputs.get("y32", False)  # barra terminada
    y33 = outputs.get("y33", False)  # fin proceso
    y42 = outputs.get("y42", False)  # flanco de subida -> inicio barra

    state = timers[robot_id]
    now = time.time()

    # Inicio timer total con y30
    if y30 and not state["running"]:
        state["total_start"] = now
        state["total_end"] = None
        state["running"] = True
        state["complete"] = False
        state["bars"] = []
        state["current_bar"] = None
        state["reported"] = False
        logger.info(f"Robot {robot_id}: Timer total iniciado")

    # Detectar flanco de subida en y42 (inicio barra)
    prev_y42 = state["prev_y42"]
    if y42 and not prev_y42 and state["running"]:
        state["current_bar"] = {"start": now, "end": None, "duration": None}
        logger.info(f"Robot {robot_id}: Inicio barra nueva (flanco y42)")

    # Barra terminada con y32
    if y32 and state["current_bar"] is not None and state["current_bar"]["end"] is None:
        state["current_bar"]["end"] = now
        state["current_bar"]["duration"] = now - state["current_bar"]["start"]
        state["bars"].append(state["current_bar"])
        logger.info(f"Robot {robot_id}: Barra terminada, duración: {state['current_bar']['duration']:.2f} s")
        state["current_bar"] = None

    # Fin timer total con y33
    if y33 and state["running"]:
        state["total_end"] = now
        state["running"] = False
        state["complete"] = True
        logger.info(f"Robot {robot_id}: Timer total detenido, duración total: {(state['total_end'] - state['total_start']):.2f} s")

    # Si el proceso se detiene (Stopped)
    if process_status == "Stopped" and state["running"]:
        state["total_end"] = now
        state["running"] = False
        state["complete"] = False
        logger.info(f"Robot {robot_id}: Proceso detenido, timers parados, marcado incompleto")

    # Guardar estado previo de y42 para detectar flancos en la siguiente iteración
    state["prev_y42"] = y42

    return copy.deepcopy(state)


def main():
    global redis_client, kafka_producer
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    try:
        keys = load_keys(path="common/redis_keys.yaml")
        redis_client = create_redis_client(REDIS_HOST, REDIS_PORT)
        kafka_producer = create_kafka_producer(KAFKA_BROKER)
    except Exception as e:
        logger.error(f"❌ Error inesperado al iniciar: {e}", exc_info=True)
        graceful_shutdown()

    logger.info("📡 Iniciando status_listener...")

    last_status_time = {rid: 0 for rid in ROBOT_IDS}
    last_raw_results = {rid: None for rid in ROBOT_IDS}

    time.sleep(5)

    while True:
        current_time = time.time()
        for robot_id in ROBOT_IDS:
            try:
                # Enviar resultados si cambiaron
                result_key = keys["status_listener"]["redis_result_template"].format(id=robot_id)
                raw_data = redis_client.get(result_key)
                if raw_data:
                    raw_result = json.loads(raw_data)
                    if last_raw_results.get(robot_id) != raw_result:
                        kafka_producer.send(KAFKA_TOPIC_RESPONSE, value=raw_result)
                        last_raw_results[robot_id] = raw_result  

                # Status y lógica timers
                if current_time - last_status_time[robot_id] >= STATUS_INTERVAL:
                    sensor_key = keys["status_listener"]["redis_sensor_template"].format(id=robot_id)
                    connection_key = keys["status_listener"]["redis_robot_connected"].format(id=robot_id)
                    process_status_key = keys["process_coordinator"]["process_state"]
                    process_current_key = keys["process_coordinator"]["process_current"]
                    last_status_time[robot_id] = current_time

                    raw_data = redis_client.get(sensor_key)
                    if raw_data:
                        raw_status = json.loads(raw_data)

                        # Detectar desconexión
                        if redis_client.get(connection_key) is None:
                            logger.error(f"⚠️ Robot {robot_id} desconectado")
                            raw_status["status"]["status"]["alarm_code"] = [9001]

                        process_status = redis_client.get(process_status_key)
                        process_current = redis_client.get(process_current_key)
                        raw_status.setdefault("process_status", {})

                        if process_status is not None:
                            bit_green = process_status == "Running"
                            bit_yellow = process_status == "Paused"
                            bit_red = process_status == "Stopped"

                            if process_status not in ["Running", "Paused", "Stopped"]:
                                bit_green = bit_yellow = bit_red = False

                            if process_status == "Terminated":
                                # NO borramos process_current según tu pedido
                                pass

                            raw_status["process_status"]["state"] = process_status
                            raw_status["process_status"]["current"] = process_current
                            raw_status["process_status"]["bit_green"] = bit_green
                            raw_status["process_status"]["bit_yellow"] = bit_yellow
                            raw_status["process_status"]["bit_red"] = bit_red
                        else:
                            raw_status["process_status"] = {"bit_green": False, "bit_yellow": False, "bit_red": False}

                        # Actualizar timers
                        timing_data = update_timers(robot_id, raw_status, process_status)

                        # Aquí NO actualizamos Redis con timing_data para no pisar process_current

                        # Publicar reporte consolidado solo al finalizar proceso y solo una vez
                        state = timers[robot_id]
                        if (state["complete"] or process_status == "Stopped") and not state["reported"]:
                            report = {
                                "robot_id": robot_id,
                                "timestamp": timing_data["total_end"] or time.time(),
                                "complete": timing_data["complete"],
                                "total_duration": (timing_data["total_end"] - timing_data["total_start"]) if timing_data["total_start"] and timing_data["total_end"] else None,
                                "bars": timing_data["bars"],
                                "process_status": process_status,
                                "process_current": process_current
                            }
                            kafka_producer.send(KAFKA_TOPIC_RESPONSE, value=report)
                            logger.info(f"Robot {robot_id}: Reporte consolidado publicado en topic response: {report}")
                            timers[robot_id]["reported"] = True

                        # Enviar status normal sin timing adicional
                        kafka_producer.send(KAFKA_TOPIC_STATUS, value=raw_status)

                    else:
                        logger.warning(f"⚠️ No se encontró status para robot {robot_id}")

            except (json.JSONDecodeError, KeyError, TypeError) as known_error:
                logger.error(f"⚠️ Datos mal formados para {robot_id}: {known_error}", exc_info=True)
            except Exception as fatal_error:
                logger.error(f"❌ Error inesperado con {robot_id}: {fatal_error}", exc_info=True)
                graceful_shutdown()

if __name__ == "__main__":
    main()
