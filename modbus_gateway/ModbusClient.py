import logging, yaml
from datetime import datetime

from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder

logger = logging.getLogger(__name__)

DTYPE_SIZES = {
    "bool":   1,     # coils
    "uint16": 1,
    "int16":  1,
    "uint32": 2,
    "int32":  2,
    "float32":2,
}

class ModbusClient:
    def __init__(self, kafka_producer, kafka_topic="orders.to_robots", config_path="config.yaml"):
        self.kafka_producer = kafka_producer
        self.kafka_topic = kafka_topic
        self.values = {}
        self.prev_triggers = {}

        self.config = self.load_config(config_path)
        self.mbconf = self.config.get("modbus", {})
        self.client = self._connect()
        # En Modbus no hay “nodos”; guardamos el mapa tal cual
        self.node_map = self.config["opc_nodes"]["read"]

        # Endianness
        self.word_order = self.mbconf.get("word_order", "high_low")
        self.byte_order = self.mbconf.get("byte_order", "big")
        self.unit_id = int(self.mbconf.get("unit_id", 1))

    # ---------- config ----------
    def load_config(self, path):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _connect(self):
        mode = self.mbconf.get("mode", "tcp").lower()
        if mode == "tcp":
            host = self.mbconf.get("host", "127.0.0.1")
            port = int(self.mbconf.get("port", 502))
            client = ModbusTcpClient(host=host, port=port)
        else:
            client = ModbusSerialClient(
                method="rtu",
                port=self.mbconf.get("serial_port", "/dev/ttyUSB0"),
                baudrate=int(self.mbconf.get("baudrate", 115200)),
                parity=self.mbconf.get("parity", "N"),
                stopbits=int(self.mbconf.get("stopbits", 1)),
                bytesize=int(self.mbconf.get("bytesize", 8)),
                timeout=2
            )
        if not client.connect():
            raise RuntimeError("No se pudo conectar a Modbus")
        return client

    def disconnect(self):
        try:
            self.client.close()
        except Exception:
            pass

    # ---------- helpers ----------
    def _endianness(self):
        byte_endian = Endian.Big if self.byte_order == "big" else Endian.Little
        # El “orden de palabra” para 32/64 bit
        word_endian = Endian.Big if self.word_order == "high_low" else Endian.Little
        return byte_endian, word_endian

    def _decode_registers(self, regs, dtype):
        byte_endian, word_endian = self._endianness()
        decoder = BinaryPayloadDecoder.fromRegisters(regs, byteorder=byte_endian, wordorder=word_endian)
        if dtype == "uint16":   return regs[0] & 0xFFFF
        if dtype == "int16":    return decoder.decode_16bit_int()
        if dtype == "uint32":   return decoder.decode_32bit_uint()
        if dtype == "int32":    return decoder.decode_32bit_int()
        if dtype == "float32":  return decoder.decode_32bit_float()
        raise ValueError(f"dtype no soportado: {dtype}")

    def _encode_value(self, val, dtype):
        byte_endian, word_endian = self._endianness()
        b = BinaryPayloadBuilder(byteorder=byte_endian, wordorder=word_endian)
        if dtype == "uint16":   b.add_16bit_uint(int(val))
        elif dtype == "int16":  b.add_16bit_int(int(val))
        elif dtype == "uint32": b.add_32bit_uint(int(val))
        elif dtype == "int32":  b.add_32bit_int(int(val))
        elif dtype == "float32":b.add_32bit_float(float(val))
        else:
            raise ValueError(f"dtype no soportado: {dtype}")
        return b.to_registers()

    # ---------- read ----------
    def read_all_inputs(self):
        for name, cfg in self.node_map.items():
            mb = cfg.get("modbus", {})
            kind = mb.get("kind")
            fc   = int(mb.get("fc", 3))
            addr = int(mb.get("addr"))
            dtype= mb.get("dtype", "uint16")
            length = int(mb.get("length", DTYPE_SIZES.get(dtype, 1)))

            try:
                if kind == "coil":
                    # FC01 Read Coils
                    rr = self.client.read_coils(addr, length, slave=self.unit_id) if fc == 1 else self.client.read_discrete_inputs(addr, length, slave=self.unit_id)
                    if rr.isError(): raise RuntimeError(rr)
                    val = bool(rr.bits[0]) if length == 1 else rr.bits[:length]
                elif kind == "holding":
                    # FC03 Read Holding Registers (o FC04 si fuesen input regs)
                    rr = self.client.read_holding_registers(addr, length, slave=self.unit_id) if fc == 3 else self.client.read_input_registers(addr, length, slave=self.unit_id)
                    if rr.isError(): raise RuntimeError(rr)
                    regs = rr.registers
                    val = self._decode_registers(regs, dtype) if length > 1 or dtype != "uint16" else regs[0]
                else:
                    logger.warning(f"Tipo modbus desconocido en {name}: {kind}")
                    continue

                self.handle_read(name, val)
            except Exception as e:
                logger.error(f"Error leyendo {name} @ {addr}: {e}", exc_info=True)

    def handle_read(self, name, val):
        config = self.config["opc_nodes"]["read"].get(name)
        if not config:
            return

        type_str = config["type"]

        if type_str == 'data':
            self.values[name] = val
        elif type_str in ['method', 'proceso']:
            prev = self.prev_triggers.get(name, False)
            now  = bool(val)
            if not prev and now:
                self.prev_triggers[name] = True
                payload = self.generate_payload(name, config, now)
                logger.info(f"📦 Payload generado: {payload}")
                if self.kafka_producer:
                    resp = self.kafka_producer.send(self.kafka_topic, value=payload)
                    logger.info(f"📦 Enviado a Kafka [{self.kafka_topic}]: {resp}")
            elif not now:
                self.prev_triggers[name] = False
        elif type_str == "bridge":
            prev = self.prev_triggers.get(name, None)
            if val != prev:
                self.prev_triggers[name] = val
                payload = self.generate_payload(name, config, val)
                logger.info(f"📦 Payload generado: {payload}")
                if self.kafka_producer:
                    resp = self.kafka_producer.send(self.kafka_topic, value=payload)
                    logger.info(f"📦 Enviado a Kafka [{self.kafka_topic}]: {resp}")

    # ---------- payload ----------
    def generate_payload(self, name, config, val):
        type_str = config['type']
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')

        if type_str == "proceso":
            keys = ["long_caja", "ancho_caja", "altura_caja", "long_barra", "ancho_barra", "espesor",
                    "peso", "cantidad_x", "cantidad_z", "no_carro", "w1", "w2"]
            params = {k: self.values.get(k) for k in keys}
        elif type_str == "bridge":
            params = config.get("param", {}).copy()
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

    # ---------- write single ----------
    def write_point(self, entry, value):
        """Escribe un punto usando la definición modbus de `entry` (dict)."""
        kind  = entry["kind"]
        fc    = int(entry.get("fc", 6))
        addr  = int(entry["addr"])
        dtype = entry.get("dtype", "uint16")

        try:
            if kind == "coil":
                # FC05: write single coil
                rr = self.client.write_coil(addr, bool(value), slave=self.unit_id)
                if rr.isError(): raise RuntimeError(rr)
            else:
                # holding
                if fc == 6:  # single register
                    regs = self._encode_value(value, "uint16" if dtype in ("uint16","int16") else dtype)
                    rr = self.client.write_register(addr, regs[0], slave=self.unit_id)
                    if rr.isError(): raise RuntimeError(rr)
                elif fc == 16:  # multiple registers
                    regs = self._encode_value(value, dtype)
                    rr = self.client.write_registers(addr, regs, slave=self.unit_id)
                    if rr.isError(): raise RuntimeError(rr)
                else:
                    raise ValueError(f"FC no soportada para write holding: {fc}")
            logger.info(f"✅ Escrito @{addr} ({dtype}) = {value}")
        except Exception as e:
            logger.warning(f"⚠️ Fallo al escribir @ {addr}: {e}")

    # ---------- write batch (como tu write_values) ----------
    def write_values(self, robot_key, values, write_map):
        if robot_key not in write_map:
            logger.warning(f"⚠️ Robot {robot_key} no encontrado en YAML")
            return

        for key, val in values.items():
            entry = write_map[robot_key].get(key)
            if not entry:
                logger.debug(f"⏭️ Clave {key} no definida en YAML para {robot_key}")
                continue
            try:
                self.write_point(entry, val)
            except Exception as e:
                logger.error(f"❌ Error preparando/escribiendo {key}: {e}", exc_info=True)
