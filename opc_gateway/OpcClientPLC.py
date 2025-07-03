from opcua import Client
from datetime import datetime

import yaml


class OpcClient:
    def __init__(self, endpoint, kafka_producer, kafka_topic="orders.to_robots", config_path="config.yaml"):
        self.client = Client(endpoint)
        self.client.name = "Python PLC Gateway"
        #self.client.session_timeout = 300000 # 5 minutes
        self.client.connect()
        self.config = self.load_config(config_path)
        self.node_map = self.init_nodes()
        self.sub_handler = self.SubHandler(self)
        self.values = {}
        self.first_trigger_skipped = set()
        self.kafka_producer = kafka_producer
        self.kafka_topic = kafka_topic
        self.handle_data_change = None

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
            print(f"Error al inicializar los nodos: {e}")
        return nodes

    def subscribe_bits(self):
        # Creamos una sola suscripción
        self.sub = self.client.create_subscription(500, self.sub_handler)

        # Creamos una lista de nodos
        monitored_nodes = []
        self.name_map = {}  # Mapea NodeId -> nombre lógico
        self.type_map = {}  # Mapea NodeId -> tipo

        for name, config in self.config['read'].items():
            if isinstance(config, dict):
                node = self.client.get_node(config['node_id'])
                monitored_nodes.append(node)
                self.name_map[node.nodeid] = name
                self.type_map[node.nodeid] = config['type']

        self.handle_data_change = self.sub.subscribe_data_change(monitored_nodes)

    def read_all_inputs(self):
        data = {}
        for name, node in self.node_map.items():
            #print(f"📊 {name} {node}:", type(node))
            data[name] = node.get_value()
            #print(data[name])
        return data

    def disconnect(self):
        if self.handle_data_change:
            self.sub.unsubscribe(self.handle_data_change)
            self.sub.delete()
        self.client.disconnect()

    class SubHandler:
        def __init__(self, outer):
            self.outer = outer

        def datachange_notification(self, node, val, data):
            name = self.outer.name_map.get(node.nodeid)
            type_str = self.outer.type_map.get(node.nodeid)
        
            if name not in self.outer.first_trigger_skipped and type_str == 'method':
                self.outer.first_trigger_skipped.add(name)
                return            

            if type_str == 'data':
                print(f"📥 Dato actualizado: {name}")
                self.outer.values[name] = val 
                print(self.outer.values)

            elif (type_str in ['method', 'proceso']) and val is True:
                payload = self.generate_payload(name, type_str)
                print(f"📦 Orden generada: {name} | {payload}")
                if self.outer.kafka_producer:
                    response = self.outer.kafka_producer.send(self.outer.kafka_topic, value=payload)
                    print(f"📦 Orden enviada a Kafka [{self.outer.kafka_topic}]: {response}")

        def generate_payload(self, name, type_str="method"):
            #     pick = [1654.937, -125.636, 1100, 180, 0, -151]
            #     put = [2476.343, -125.616, 822.786, 180, 0, -151]

            timestamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
            params = {}
            if type_str == "proceso":
                params = {
                    "ancho_caja": self.outer.values["ancho_caja"],
                    "long_barra": self.outer.values["long_barra"],
                    "ancho_barra": self.outer.values["ancho_barra"],
                    "espesor": self.outer.values["espesor"],
                    "peso": self.outer.values["peso"],
                    "cantidad": self.outer.values["cantidad"],
                    "no_carro": self.outer.values["no_carro"]
                }                

            enriched = {
                "order_id": f"ORD_{timestamp}_borunte",
                "type": "method",
                "name": name,
                "params": params,
                "timestamp": timestamp
            }
            return enriched

        
