from kafka import KafkaConsumer
from JsonBorunteClient import JSONBorunteClient

import json, time, os, logging, socket


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("ModbusBorunteClient")

PROCESS_ID = os.getenv("PROCESS_ID", "kafka_to_mode_bridge")
BORUNTE_IP_01 = os.getenv("BORUNTE_IP", "192.168.100.20")
#BORUNTE_IP_02 = os.getenv("BORUNTE_IP", "192.168.100.22")
#TARGET_ID = os.getenv("TARGET_ID", "borunte_test_01")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC_COMMANDS = os.getenv("KAFKA_TOPIC_COMMANDS", "robot.commands")
KAFKA_TOPIC_STATUS = os.getenv("KAFKA_TOPIC_STATUS", "robot.status")
KAFKA_TOPIC_RESPONSES = os.getenv("KAFKA_TOPIC_RESPONSES", "robot.responses")
KAFKA_RETRY = int(os.getenv("KAFKA_RETRY", 30))
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "socket_bridge_group")
STATUS_RATE = int(os.getenv("STATUS_RATE", 5))


def crear_kafka_consumer():
    consumer = KafkaConsumer(
        KAFKA_TOPIC_COMMANDS,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id=GROUP_ID,
        auto_offset_reset='latest',
        enable_auto_commit=True
    )
    return consumer

def wait_for_kafka(broker="localhost:9092", retries=30, timeout=90):
    host, port = broker.split(":")
    print(f"🔍 Esperando que Kafka esté disponible en {host}:{port}...")
    for attempt in range(retries):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                print("✅ Puerto Kafka activo, iniciando productor")
                return
        except (socket.timeout, ConnectionRefusedError):
            print(f"⏳ Kafka no responde (intento {attempt+1}/{retries})...")
            time.sleep(3)
    raise RuntimeError("❌ Kafka no se conectó tras múltiples intentos")

def crear_robots():
    robot_01 = JSONBorunteClient(host=BORUNTE_IP_01, target_id="borunte_test_01")
    #robot_01.connect()
    #robot_02 = JSONBorunteClient(host=BORUNTE_IP_02, target_id="borunte_test_02")
    #robot_02.connect()
    robot = {
        robot_01.target_id: robot_01,
        #robot_02.target_id: robot_02
    }
    return robot

def main():    
    consumer = crear_kafka_consumer()
    robots = crear_robots()
    
    for robot_id, robot in robots.items():
        robot.connect()
        print(f"🟢 Robot {robot_id} connected")

    logger.info("🟢 Lectura de comandos iniciada.")
    for msg in consumer:
        #key = msg.key.decode() if msg.key else None
        data = msg.value

        # if key != TARGET_ID:
        #     continue
        #print(f"📦 Orden recibida: {data}")
        order_id = data["order_id"]
        method_name = data["name"]
        params = data.get("params", [])
        if data["target_id"] not in robots.keys():
            logger.warning(f"⛔ Robot no encontrado: {data['target_id']}")
            continue
        
        target_id = data["target_id"]
        robot = robots[target_id]

        print(f"📦 Orden recibida: {order_id} - {method_name} - {params}")
        try:           
            if "start_button" == method_name:  
                result = robot.start_button()
            elif "pause_button" == method_name:
                result = robot.action_pause()
                logger.info(f"🔧 Resultado: {result}")
            elif "stop_button" == method_name:
                result = robot.action_stop()
            elif "clear_alarm_button" == method_name:
                result = robot.clear_alarm()
            elif "proceso" in method_name:
                result = robot.proceso_01(params)
            else:
                logger.warning(f"⛔ Método no permitido o inexistente: {method_name}")
            
            logger.info(f"🔧 Resultado: {result}")
        except:
            logger.error(f"🔴 Error en el proceso de commandos: {method_name}", exc_info=True)


if __name__ == "__main__":
    wait_for_kafka(broker=KAFKA_BROKER, retries=KAFKA_RETRY)
    main()