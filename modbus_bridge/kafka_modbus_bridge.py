from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from ModbusBorunteClient import ModbusBorunteClient, ModbusBorunteError
from pymodbus.exceptions import ModbusIOException
from datetime import datetime

import json, time, os, threading, logging, socket

# [ borunte_01 → producer ]         \
# [ borunte_02 → producer ]  ----->  kafka topic: "robot_status"
# [ borunte_03 → producer ]         /

# Estructura del mensaje:
# robot.commands
# {
#     "robot_id": "borunte_01",
#     "type": "method",
#     "name": "set_output",
#     "args": ["y13", 1],
#     "kwargs": {}
# }

# robot.status
# {
#     "robot_id": "borunte_01",
#     "ip": "127.0.0.1",
#     "online": true,
#     "status": {
#         "y13": 1
#     },
#     "timestamp": "2023-06-26T12:34:56.789Z"
# }

# robot.responses
# {
#     "robot_id": "borunte_01",
#     "type": "method",
#     "online": True,
#     "command": method_name,
#     "result": {"status": True, ...},
#     "error": None,
#     "timestamp": "2023-06-26T12:34:56.789Z"
# }

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("ModbusKafkaBridge")

# Variables de entorno con valores por defecto
BORUNTE_IP = os.getenv("BORUNTE_IP", "127.0.0.1")
ROBOT_ID = os.getenv("ROBOT_ID", "borunte_01")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC", "robot.commands")
KAFKA_TOPIC_STATUS = os.getenv("KAFKA_STATUS_TOPIC", "robot.status")
KAFKA_TOPIC_RESPONSES = os.getenv("KAFKA_RESP_TOPIC", "robot.responses")
KAFKA_WAIT_TIME = int(os.getenv("KAFKA_WAIT_TIME", 5))
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "modbus_bridge_group")
STATUS_RATE = int(os.getenv("STATUS_RATE", 5))


def crear_modbus_robot():
    robot = ModbusBorunteClient(host=BORUNTE_IP)
    if robot.connect():
        logger.info(f"Conectado a robot BORUNTE en {BORUNTE_IP}")
        return robot
    logger.warning("No se pudo conectar al robot.")
    return None

def crear_kafka_consumer():
    consumer = KafkaConsumer(
        KAFKA_TOPIC_COMMANDS,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id=GROUP_ID
    )
    return consumer

def crear_kafka_producer():
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda m: json.dumps(m).encode('utf-8')
    )
    return producer

def emitir_status_periodico(robot, producer, stop_event):
    logger.info("🟢 Hilo de status iniciado.")
    while not stop_event.is_set():
        try:
            data = robot.read_all_borunte_data()
            payload = {
                "robot_id": ROBOT_ID,
                "ip": BORUNTE_IP,
                "online": True,
                "status": data,
                "timestamp": datetime.now().isoformat() + "Z"
            }
            producer.send(KAFKA_TOPIC_STATUS, key=ROBOT_ID, value=payload)
            logger.info("📡 Status enviado al broker Kafka.")
        except Exception as e:
            logger.error(f"Error en hilo de status: {e}")
            offline_payload = {
                "robot_id": ROBOT_ID,
                "ip": BORUNTE_IP,
                "online": robot.health_check(),
                "status": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
            try:
                producer.send(KAFKA_TOPIC_STATUS, key=ROBOT_ID, value=offline_payload)
                logger.warning("📴 Robot marcado como OFFLINE.")
            except Exception as send_error:
                logger.error(f"No se pudo enviar mensaje OFFLINE: {send_error}")
            stop_event.set()  # Detiene el hilo si no se puede leer
            break
        
        stop_event.wait(STATUS_RATE)
    
    logger.info("🔴 Hilo de status detenido.")

def wait_for_kafka(host, port=9092, timeout=90):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                logger.info(f"✅ Kafka disponible en {host}:{port}")
                break
        except OSError as e:
            if time.time() - start_time > timeout:
                logger.error(f"❌ Timeout esperando Kafka en {host}:{port}")
                raise RuntimeError(f"Kafka no disponible en {host}:{port} tras {timeout} segundos")
            logger.warning(f"⏳ Esperando Kafka en {host}:{port}...")
            time.sleep(2)


robot = None
status_thread = None
status_stop_event = None

kafka_host, kafka_port = KAFKA_BROKER.split(":")
wait_for_kafka(host=kafka_host, port=int(kafka_port), timeout=KAFKA_WAIT_TIME)

producer = crear_kafka_producer()
consumer = crear_kafka_consumer()

while True:
    try:
        if not robot:
            logger.warning("🧠 Intentando reconectar al robot BORUNTE...")
            robot = crear_modbus_robot()
            if not robot:
                time.sleep(5)
                continue

            if status_thread and status_thread.is_alive():
                status_stop_event.set()
                status_thread.join()

            status_stop_event = threading.Event()
            status_thread = threading.Thread(
                target=emitir_status_periodico,
                args=(robot, producer, status_stop_event),
                daemon=True
            )
            status_thread.start()

        logger.info(f"Esperando comandos en topic Kafka '{KAFKA_TOPIC_COMMANDS}' para {ROBOT_ID}...")

        for msg in consumer:
            key = msg.key.decode() if msg.key else None
            data = msg.value

            if key != ROBOT_ID:
                continue

            method_name = data["name"]
            args = data.get("args", [])
            kwargs = data.get("kwargs", {})

            if not method_name.startswith('_') and hasattr(robot, method_name):
                method = getattr(robot, method_name)
                try:
                    logger.info(f"🔧 Ejecutando método: {method_name}({args}, {kwargs})")
                    result = method(*args, **kwargs)
                    response = {
                        "robot_id": ROBOT_ID,
                        "ip": BORUNTE_IP,
                        "online": True,
                        "command": method_name,
                        "result": result,
                        "error": None,
                        "timestamp": datetime.now().isoformat() + "Z"
                    }
                    producer.send(KAFKA_TOPIC_RESPONSES, key=ROBOT_ID, value=response).get(timeout=5)
                    logger.info(f"✅ Método ejecutado: {method_name}")
                except Exception as e:
                    logger.error(f"❌ Error al ejecutar '{method_name}': {e}")
                    response = {
                        "robot_id": ROBOT_ID,
                        "ip": BORUNTE_IP,
                        "online": robot.health_check(),
                        "command": method_name,
                        "result": None,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat() + "Z"
                    }
                    producer.send(KAFKA_TOPIC_RESPONSES, key=ROBOT_ID, value=response).get(timeout=5)
            else:
                logger.warning(f"⛔ Método no permitido o inexistente: {method_name}")


    except KafkaError as e:
        logger.error(f"🧯 Error de Kafka: {e}")
        try: 
            producer.close()
            consumer.close()
        except Exception as close_err:
            logger.error(f"❌ No se pudo cerrar Kafka: {close_err}")

        time.sleep(5)

        try:
            producer = crear_kafka_producer()
            consumer = crear_kafka_consumer()
        except Exception as create_err:
            logger.error(f"❌ No se pudo crear Kafka: {create_err}")

    except ModbusIOException as e:
        logger.error(f"💥 Error Modbus: {e}")
        if robot:
            robot.close()
        robot = None
        if status_stop_event:
            status_stop_event.set()

        try:
            offline_payload = {
                "robot_id": ROBOT_ID,
                "ip": BORUNTE_IP,
                "online": False,
                "status": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
            producer.send(KAFKA_TOPIC_STATUS, key=ROBOT_ID, value=offline_payload).get(timeout=5)
            logger.warning("📴 Robot marcado como OFFLINE.")
        except Exception as send_err:
            logger.error(f"❌ No se pudo enviar estado OFFLINE: {send_err}")

    except ModbusBorunteError as e:
        logger.error(f"🚫 Error ModbusBorunte: {e}")
        response = {
            "robot_id": ROBOT_ID,
            "ip": BORUNTE_IP,
            "online": robot.health_check(),
            "command": "ModbusBorunteError",
            "result": {},
            "error": str(e),
            "timestamp": datetime.now().isoformat() + "Z"
        }
        try:
            producer.send(KAFKA_TOPIC_RESPONSES, key=ROBOT_ID, value=response).get(timeout=5)
        except Exception as send_err:
            logger.error(f"❌ No se pudo enviar respuesta de error: {send_err}")

        