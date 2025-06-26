# opc_client.py
from opcua import Client, ua
import yaml
from datetime import datetime


class OpcClient:
    def __init__(self, endpoint, kafka_producer, kafka_topic="orders.to_robots", config_path="config.yaml"):
        self.client = Client(endpoint)
        self.client.connect()
        self.config = self.load_config(config_path)
        self.node_map = self.init_nodes()
        self.sub_handler = self.SubHandler(self)
        self.values = {}
        self.first_trigger_skipped = set()
        self.kafka_producer = kafka_producer
        self.kafka_topic = kafka_topic

    def load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)['opc_nodes']

    def init_nodes(self):
        nodes = {}
        try:
            for name, node_info in self.config['read'].items():
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

        self.sub.subscribe_data_change(monitored_nodes)

    def read_all_inputs(self):
        data = {}
        for name, node in self.node_map.items():
            print(f"📊 {name} {node}:", type(node))
            data[name] = node.get_value()
            print(data[name])
        return data

    def disconnect(self):
        self.sub.unsubscribe(self.sub_handler)
        self.client.disconnect()

    class SubHandler:
        def __init__(self, outer):
            self.outer = outer

        def datachange_notification(self, node, val, data):
            name = self.outer.name_map.get(node.nodeid)
            type_str = self.outer.type_map.get(node.nodeid)
            
            print(f"📊 {name} {node}:", val)
            if name not in self.outer.first_trigger_skipped and type_str == 'method':
                self.outer.first_trigger_skipped.add(name)
                print(f"⏩ Ignorando primer evento de {name} (valor actual: {val})")
                return
            
            if type_str == 'method' and val is True:
                print(f"📥 Método activado: {name}")
                no_robot = self.outer.values["no_robot"]
                for i in range(0, no_robot):    
                    payload = self.generate_payload(name, i)
                    print("📦 Orden generada:", payload)
                    if self.outer.kafka_producer:
                        response = self.outer.kafka_producer.send(self.outer.kafka_topic, value=payload)
                        print(f"📦 Orden enviada a Kafka [{self.outer.kafka_topic}]: {response}")
            elif type_str == 'data':
                print(f"📥 Dato recibido: {name}")
                self.outer.values[name] = val 
                print(self.outer.values)

        def generate_payload(self, name, no_robot):
            timestamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
            if no_robot == 1:
                pick = [1654.937, -125.636, 1100, 180, 0, -151]
                put = [2476.343, -125.616, 822.786, 180, 0, -151]
            elif no_robot == 2:
                pick = [1654.937, -125.636, 1100, 180, 0, -151]
                put = [2476.343, -125.616, 822.786, 180, 0, -151]
            else:
                pick = [0,0,0,0,0, 0]
                put = [0,0,0,0,0, 0]
            enriched = {
                "order_id": f"ORD_{timestamp}_borunte_test_{no_robot:02d}",
                "target_device": f"borunte_test_{no_robot:02d}",
                "type": "method",
                "name": name,
                "params": {
                    "pick": pick,
                    "put": put,
                    "cantidad": self.outer.values["cantidad"],
                    "dx": self.outer.values["dx1"],
                    "dy": self.outer.values["dy1"],
                    "altura": self.outer.values["espesor"],
                    "velocidad": self.outer.values["velocidad"]
                }
            }
            return enriched

        
