from kafka import KafkaConsumer
from OpcClientPLC import OpcClient
import os, json, logging, signal, sys, yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger("KafkaStatusToOPC")

# Config
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC_STATUS = os.getenv("KAFKA_TOPIC_STATUS", "robot.status")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "opc_writer_group")
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator")

opc_nodes = {}
consumer = None
opc = None

def graceful_shutdown(sig=None, frame=None):
    logger.info("🛑 Cerrando conexiones...")
    try:
        if opc:
            opc.disconnect()
            logger.info("✅ Cliente OPC desconectado")
        if consumer:    
            consumer.close()
            logger.info("✅ Kafka consumer cerrado")
    except Exception as e:
        logger.warning(f"Error cerrando conexiones: {e}", exc_info=True)
    sys.exit(0)

def create_kafka_consumer(topic, broker, group_id):
    return KafkaConsumer(
        topic, 
        bootstrap_servers=[broker], 
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id=group_id,
        auto_offset_reset='latest',
        enable_auto_commit=True
    )

def cargar_nodos_escritura(path):
    with open(path, "r") as f:
        return yaml.safe_load(f).get("opc_nodes", {}).get("write", {})

def parsear_status(status_dict):
    status_data = {}
    status = status_dict.get("status", {})
    status_info = status.get("status", {})

    status_data["running"] = 1 if status_dict.get("movement_status") else 0
    status_data["alarm_code"] = status_info.get("alarm_code", [0])[0]
    count = status.get("counters")
    count_total = int(count["counter-0"]["current"]) + int(count["counter-1"]["current"])
    status_data["stack_count"] = count_total

    # "axis_torque": [0.0,0.0,0.0,0.0,0.0,0.0]
    # torque_info = status_info.get("axis_torque")
    # for i, val in enumerate(torque_info):
    #     status_data[f"j{i+1}"] = val

    return status_data

def escribir_variables_opc(client, robot_key, values, node_map):
    if robot_key not in node_map:
        logger.warning(f"⚠️ Robot {robot_key} no encontrado en YAML")
        return

    for key, val in values.items():
        node_id = node_map[robot_key].get(key)
        if node_id:
            try:
                node = client.client.get_node(node_id)
                node.set_value(val)
                #logger.info(f"✅ {key} = {val} escrito en {node_id}")
            except Exception as e:
                logger.error(f"❌ Error al escribir {key}: {e}")
        else:
            logger.debug(f"⏭️ Clave {key} no definida en YAML para {robot_key}")

def main():
    global consumer, opc_nodes, opc
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    opc_nodes = cargar_nodos_escritura(path="config.yaml")
    if not opc_nodes:
        logger.error("❌ No se encontraron variables 'write' en el YAML")
        sys.exit(1)

    consumer = create_kafka_consumer(KAFKA_TOPIC_STATUS, KAFKA_BROKER, KAFKA_GROUP_ID)
    opc = OpcClient(OPC_ENDPOINT, kafka_producer=None)
    logger.info(f"📡 Esperando mensajes en topic '{KAFKA_TOPIC_STATUS}'...")

    for msg in consumer:
        data = msg.value
        #logger.info(f"📥 Mensaje Kafka recibido: {data}")
        try:
            robot_id = data.get("robot_id")
            if robot_id != "01":
                logger.warning("⚠️ robot_id no válido")
                continue

            robot_key = f"robot{int(robot_id)}"
            status_data = parsear_status(data)
            
            escribir_variables_opc(opc, robot_key, status_data, opc_nodes)
            #opc.disconnect()

        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}", exc_info=True)

if __name__ == "__main__":
    main()
