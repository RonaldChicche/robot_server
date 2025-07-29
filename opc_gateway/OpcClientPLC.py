from opcua import Client
from opcua import ua
from datetime import datetime

import yaml, logging

logger = logging.getLogger(__name__)

class OpcClient:
    def __init__(self, endpoint, kafka_producer, kafka_topic="orders.to_robots", config_path="config.yaml"):
        self.client = Client(endpoint)
        self.client.name = "Python PLC Gateway"
        self.client.connect()
        self.config = self.load_config(config_path)
        self.node_map = self.init_nodes()
        self.kafka_producer = kafka_producer
        self.kafka_topic = kafka_topic
        self.values = {}
        self.prev_triggers = {}

    def load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)['opc_nodes']

    def init_nodes(self):
        nodes = {}
        try:
            for name, node_info in reversed(list(self.config['read'].items())):
                node_id = node_info['node_id']
                nodes[name] = self.client.get_node(node_id)
        except Exception as e:
            logger.error(f"⚠️ Error al inicializar los nodos: {e}", exc_info=True)
        return nodes

    def read_all_inputs(self):
        for name, node in self.node_map.items():
            val = node.get_value()
            self.handle_read(name, val)
        
    def handle_read(self, name, val):
        config = self.config['read'].get(name)
        if not config:
            return

        type_str = config['type']

        if type_str == 'data':
            self.values[name] = val
        elif type_str in ['method', 'proceso']:
            prev = self.prev_triggers.get(name, False)
            if not prev and val is True:
                self.prev_triggers[name] = True
                payload = self.generate_payload(name, config, val)
                logger.info(f"📦 Payload generado: {payload}")
                if self.kafka_producer:
                    response = self.kafka_producer.send(self.kafka_topic, value=payload)
                    logger.info(f"📦 Enviado a Kafka [{self.kafka_topic}]: {response}")
            elif val is False:
                self.prev_triggers[name] = False
        elif type_str in ["bridge"]:
            prev = self.prev_triggers.get(name, False)
            if val != prev:
                self.prev_triggers[name] = val
                payload = self.generate_payload(name, config, val)
                logger.info(f"📦 Payload generado: {payload}")
                if self.kafka_producer:
                    response = self.kafka_producer.send(self.kafka_topic, value=payload)
                    logger.info(f"📦 Enviado a Kafka [{self.kafka_topic}]: {response}")

    def disconnect(self):
        self.client.disconnect()

    def generate_payload(self, name, config, val):
        type_str = config['type']
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')

        if type_str == "proceso":
            params = {
                key: self.values[key]
                for key in [
                    "long_caja", "ancho_caja", "long_barra", "ancho_barra", "espesor",
                    "peso", "cantidad_x", "cantidad_z", "no_carro"
                ]
            }
        elif type_str == "bridge":
            params = config.get("param", {})
            type_str = "method"
            params["value"] = val
        else:
            params = {}

        return {
            "order_id": f"ORD_{timestamp}_borunte",
            "type": type_str,
            "name": config.get("name", name),
            "params": params,
            "timestamp": timestamp
        }
    
    def write_node(self, node_id_str, value):
        node = self.client.get_node(node_id_str)
        variant_type = node.get_data_type_as_variant_type()

        wv = ua.WriteValue()
        wv.NodeId = node.nodeid
        wv.AttributeId = ua.AttributeIds.Value
        wv.Value = ua.DataValue(ua.Variant(value, variant_type))

        params = ua.WriteParameters()
        params.NodesToWrite = [wv]

        result = self.client.uaclient.write(params)
        if result[0].is_good():
            logger.info(f"✅ Nodo {node_id_str} escrito correctamente con valor {value}")
        else:
            logger.warning(f"⚠️ Fallo al escribir nodo {node_id_str}: {result[0]}")

    
    def write_values(self, robot_key, values, write_map):
        if robot_key not in write_map:
            logger.warning(f"⚠️ Robot {robot_key} no encontrado en YAML")
            return

        write_values = []

        for key, val in values.items():
            node_id_str = write_map[robot_key].get(key)
            if not node_id_str:
                logger.debug(f"⏭️ Clave {key} no definida en YAML para {robot_key}")
                continue

            try:
                node = self.client.get_node(node_id_str)
                variant_type = node.get_data_type_as_variant_type()

                wv = ua.WriteValue()
                wv.NodeId = node.nodeid
                wv.AttributeId = ua.AttributeIds.Value
                wv.Value = ua.DataValue(ua.Variant(val, variant_type))

                write_values.append(wv)
            except Exception as e:
                logger.error(f"❌ Error preparando {key}: {e}", exc_info=True)

        if write_values:
            try:
                params = ua.WriteParameters()
                params.NodesToWrite = write_values

                result = self.client.uaclient.write(params)
                for idx, res in enumerate(result):
                    key = list(values.keys())[idx]
                    if res.is_good():
                        logger.info(f"✅ {key} escrito correctamente")
                    else:
                        logger.warning(f"⚠️ Fallo al escribir {key}: {res}")
            except Exception as e:
                logger.error(f"❌ Error al escribir OPC UA: {e}", exc_info=True)
