from OpcClientPLC import OpcClient
from opcua import ua
import os, json, logging, signal, sys, yaml, time, redis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logging.getLogger("opcua.client.ua_client").setLevel(logging.WARNING)
logging.getLogger("opcua.uaprotocol").setLevel(logging.WARNING)

logger = logging.getLogger("RedisStatusToOPC")

# Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_KEY_STATUS = os.getenv("REDIS_KEY_STATUS", "robot:01:sensor_data")
REDIS_KEY_PROCESS = os.getenv("REDIS_KEY_PROCESS", "process:state")
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://ronald_desk:62640/IntegrationObjects/ServerSimulator")

opc_nodes = {}
redis_client = None
opc = None

def create_redis_client(host="localhost", port=6379):
    return redis.Redis(host=host, port=port, decode_responses=True)

def graceful_shutdown(sig=None, frame=None):
    logger.info("🛑 Cerrando conexiones...")
    try:
        if opc:
            opc.disconnect()
            logger.info("✅ Cliente OPC desconectado")
    except Exception as e:
        logger.warning(f"Error cerrando conexiones: {e}", exc_info=True)
    sys.exit(0)

def cargar_nodos_escritura(path):
    with open(path, "r") as f:
        return yaml.safe_load(f).get("opc_nodes", {}).get("write", {})

def parsear_status(status_dict):
    status_data = {}
    status = status_dict.get("status", {})
    status_info = status.get("status", {})

    status_data["running"] = True if status_dict.get("movement_status") else False
    status_data["terminado"] = True if status["outputs"]["y"]["y33"] else False
    status_data["set_ok"] = True if status["outputs"]["y"]["y45"] else False
    status_data["alarm_code"] = int(status_info.get("alarm_code", [0])[0])
    count = status.get("counters")
    count_total = int(count["counter-2"]["current"])
    status_data["stack_count"] = count_total
    pos_x = status_dict["status"]["status"]["world_position"][0]
    pos_y = status_dict["status"]["status"]["world_position"][1]
    pos_z = status_dict["status"]["status"]["world_position"][2]
    pos_u = status_dict["status"]["status"]["world_position"][3]
    pos_v = status_dict["status"]["status"]["world_position"][4]
    pos_w = status_dict["status"]["status"]["world_position"][5]
    status_data["pos_x"] = pos_x
    status_data["pos_y"] = pos_y
    status_data["pos_z"] = pos_z
    status_data["ang_u"] = pos_u
    status_data["ang_v"] = pos_v
    status_data["ang_w"] = pos_w

    torq_J1 = status_info["axis_torque"][0]
    torq_J2 = status_info["axis_torque"][1]
    torq_J3 = status_info["axis_torque"][2]
    torq_J4 = status_info["axis_torque"][3]
    torq_J5 = status_info["axis_torque"][4]
    torq_J6 = status_info["axis_torque"][5]
    status_data["j1"] = torq_J1
    status_data["j2"] = torq_J2
    status_data["j3"] = torq_J3
    status_data["j4"] = torq_J4
    status_data["j5"] = torq_J5
    status_data["j6"] = torq_J6

    return status_data

def escribir_variables_opc(client, robot_key, values, node_map):
    if robot_key not in node_map:
        logger.warning(f"⚠️ Robot {robot_key} no encontrado en YAML")
        return

    write_values = []

    for key, val in values.items():
        node_id_str = node_map[robot_key].get(key)
        if not node_id_str:
            logger.debug(f"⏭️ Clave {key} no definida en YAML para {robot_key}")
            continue

        node = client.client.get_node(node_id_str)
        variant_type = node.get_data_type_as_variant_type()

        wv = ua.WriteValue()
        wv.NodeId = node.nodeid
        wv.AttributeId = ua.AttributeIds.Value
        wv.Value = ua.DataValue(ua.Variant(val, variant_type))

        write_values.append(wv)

    if write_values:
        params = ua.WriteParameters()
        params.NodesToWrite = write_values

        result = client.client.uaclient.write(params)
        for idx, res in enumerate(result):
            key = list(values.keys())[idx]
            if not res.is_good():
                logger.warning(f"⚠️ Fallo al escribir {key}: {res}")

def main():
    global redis_client, opc_nodes, opc
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    try:
        opc_nodes = cargar_nodos_escritura(path="config.yaml")
        if not opc_nodes:
            logger.error("❌ No se encontraron variables 'write' en el YAML")
            sys.exit(1)

        redis_client = create_redis_client(REDIS_HOST, REDIS_PORT)
        opc = OpcClient(OPC_ENDPOINT, kafka_producer=None)
        logger.info(f"📡 Escuchando datos en Redis... {REDIS_HOST} -> {REDIS_KEY_PROCESS} -> {REDIS_KEY_STATUS}")

    except Exception as e:
        logger.error(f"❌ Error al iniciar: {e}", exc_info=True)
        graceful_shutdown()

    error_count = 0

    while True:
        try:
            raw_status = redis_client.get(REDIS_KEY_STATUS)
            if not raw_status:
                time.sleep(0.1)
                continue

            data = json.loads(raw_status)
            robot_id = data.get("robot_id")
            if robot_id != "01":
                logger.warning("⚠️ robot_id no válido")
                continue

            robot_key = f"robot{int(robot_id)}"
            status_data = parsear_status(data)
            escribir_variables_opc(opc, robot_key, status_data, opc_nodes)

            process_status = redis_client.get(REDIS_KEY_PROCESS)
            if process_status is not None:
                bit_green = process_status == "Running"
                bit_yellow = process_status == "Paused"
                bit_red = process_status == "Stopped"

                # En todos los demás casos, los bits están apagados (incluye Vacio y Terminado)
                if process_status not in ["Running", "Paused", "Stopped"]:
                    bit_green = bit_yellow = bit_red = False
            else:
                raw_status["process_status"] = {"bit_green": False, "bit_yellow": False, "bit_red": False}

            logger.info(f"Process status: {process_status}")
            opc.write_node("ns=4;i=34", bit_green)
            opc.write_node("ns=4;i=36", bit_yellow)
            opc.write_node("ns=4;i=35", bit_red)

            time.sleep(0.2)

        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error procesando datos de Redis: {e}", exc_info=True)

        if error_count >= 3:
            logger.error("🔴 Error crítico, apagando...")
            graceful_shutdown()

if __name__ == "__main__":
    main()
