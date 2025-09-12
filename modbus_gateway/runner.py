import os, json, time, signal, sys, logging, threading
from typing import Optional
import redis
from kafka import KafkaProducer

from ModbusClient import ModbusGateway  # asegúrate del nombre de archivo/clase

# ---------- Config ----------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO),
                    format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
log = logging.getLogger("runner")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "190.168.10.102")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB   = int(os.getenv("REDIS_DB", "0"))
REDIS_KEY_STATUS  = os.getenv("REDIS_KEY_STATUS", "robot:01:sensor_data")
REDIS_KEY_PROCESS = os.getenv("REDIS_KEY_PROCESS", "process:state")
REDIS_KEY_RESULT = os.getenv("REDIS_KEY_RESULT", "process:result")

# Kafka
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC     = os.getenv("KAFKA_TOPIC", "robot.commands")
KAFKA_ACKS      = os.getenv("KAFKA_ACKS", "all")
KAFKA_LINGER_MS = int(os.getenv("KAFKA_LINGER_MS", "5"))
KAFKA_CLIENT_ID = os.getenv("KAFKA_CLIENT_ID", "modbus-runner")
KAFKA_ENABLE    = os.getenv("KAFKA_ENABLE", "1").lower() in ("1","true","yes")

# Modbus
MODBUS_HOST = os.getenv("MODBUS_HOST", "0.0.0.0")
MODBUS_PORT = os.getenv("MODBUS_PORT", "5020")

# Opcionales
ENABLE_WRITE_FROM_REDIS = os.getenv("ENABLE_WRITE_FROM_REDIS", "0").lower() in ("1","true","yes")
ENABLE_STACK_LIGHTS     = os.getenv("ENABLE_STACK_LIGHTS", "0").lower() in ("1","true","yes")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0.2"))
ROBOT_KEY = os.getenv("ROBOT_KEY", "robot1")
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yaml")

# ---------- Globals ----------
stop_event = threading.Event()
gw: Optional[ModbusGateway] = None
rd: Optional[redis.Redis] = None
kafka: Optional[KafkaProducer] = None

# ---------- Helpers ----------
def shutdown(*_):
    log.info("Recibida señal de parada...")
    stop_event.set()
    try:
        if gw:
            gw.close()
    except Exception as e:
        log.warning(f"Error cerrando ModbusGateway: {e}")
    try:
        if kafka:
            kafka.flush(3.0)  # fuerza envío restante
    except Exception as e:
        log.warning(f"Error en flush Kafka: {e}")
    log.info("Bye")

def parse_status(payload: dict, payload_result: dict) -> dict:
    st = {}
    s   = payload.get("status", {})
    result_time_bar = payload_result.get("bars", 0)
    sin = s.get("status", {})

    st["running"] = 1 if payload.get("movement_status") else 0
    y = s.get("outputs", {}).get("y", {})
    st["terminado"]     = 1 if y.get("y33") else 0
    st["set_ok"]        = 1 if y.get("y45") else 0
    st["stack_ready"]   = 1 if y.get("y35") else 0
    st["layer_ready"]   = 1 if y.get("y36") else 0
    st["gripper_state"] = 1 if y.get("y23") else 0
    st["home_done"]     = 1 if y.get("y37") else 0

    st["alarm_code"] = int((sin.get("alarm_code") or [0])[0])
    cnt = s.get("counters", {})
    st["stack_count"] = int(cnt.get("counter-2", {}).get("current", 0))
    st["stack_time"] = int(result_time_bar * 1000)

    wp = sin.get("world_position", [0,0,0,0,0,0])
    st.update({
        "pos_x": float(wp[0]), "pos_y": float(wp[1]), "pos_z": float(wp[2]),
        "ang_u": float(wp[3]), "ang_v": float(wp[4]), "ang_w": float(wp[5]),
    })

    tq = sin.get("axis_torque", [0,0,0,0,0,0])
    for i in range(6):
        st[f"j{i+1}"] = float(tq[i] if i < len(tq) else 0.0)

    return st

def delivery_report(err, msg):
    if err is not None:
        log.error(f"Kafka delivery failed: {err}")
    else:
        # Debug reducido; deja INFO para cosas importantes
        log.debug(f"Kafka delivered to {msg.topic()} [{msg.partition()}] at {msg.offset()}")

def make_kafka() -> Optional[KafkaProducer]:
    #def create_kafka_producer(broker):
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
    return producer

def kafka_send(topic: str, value: dict, key: Optional[str] = None):
    if not kafka:
        return
    payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
    try:
        kafka.produce(topic=topic, key=key, value=payload, on_delivery=delivery_report)
        kafka.poll(0)  # sirve el callback
    except BufferError:
        # Cola llena: fuerza vaciado y reintenta rápido
        kafka.poll(0.5)
        kafka.produce(topic=topic, key=key, value=payload, on_delivery=delivery_report)

def main():
    global gw, rd, kafka
    signal.signal(signal.SIGINT, shutdown)
    try:
        signal.signal(signal.SIGTERM, shutdown)
    except Exception:
        pass

    # Conexiones
    kafka = make_kafka()
    rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

    gw = ModbusGateway(modbus_host=MODBUS_HOST, modbus_port=MODBUS_PORT, config_path=CONFIG_PATH, kafka_producer=kafka, kafka_topic=KAFKA_TOPIC)  # tu clase lo usará internamente

    backoff = 0.5
    backoff_max = 5.0
    log.info("loop...")
    while not stop_event.is_set():
        try:
            # 1) Estados desde Redis → Modbus (solo difs, con confirmación)
            if ENABLE_WRITE_FROM_REDIS:
                raw = rd.get(REDIS_KEY_STATUS)
                raw_result = rd.get(REDIS_KEY_RESULT)
                if raw_result is None:
                    raw_result = {"bars": 0}
                
                data_result = json.loads(raw_result)

                if raw:
                    try:
                        data = json.loads(raw)
                        if data.get("robot_id") in ("01","1"):

                            st = parse_status(data, data_result)
                            gw.write_status_diff(ROBOT_KEY, st, confirm=True)
                    except Exception as e:
                        log.warning(f"payload Redis inválido: {e}", exc_info=True)

            # 2) process:state → luces
            if ENABLE_STACK_LIGHTS:
                ps = rd.get(REDIS_KEY_PROCESS) or ""
                lights = {
                    "state_green":  1 if ps == "Running" else 0,
                    "state_yellow": 1 if ps == "Paused"  else 0,
                    "state_red":    1 if ps == "Stopped" else 0,
                }
                gw.write_status_diff(ROBOT_KEY, lights, confirm=False)

            # 3) Eventos (READ) → Kafka (tu gateway envía usando kafka_producer)
            ev = gw.poll_events_once()  # si retorna eventos, también los publicamos directo
            # if ev:
            #     # Por si tu gateway no los publica internamente:
            #     kafka_send(KAFKA_TOPIC, ev, key=ev.get("robot_id","unknown"))

            backoff = 0.5  # reset backoff al operar OK
            stop_event.wait(SLEEP_SEC)

        except Exception as e:
            log.exception(f"loop error: {e}")
            stop_event.wait(backoff)
            backoff = min(backoff * 2, backoff_max)

    shutdown()

if __name__ == "__main__":
    main()
