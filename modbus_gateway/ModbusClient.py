# modbus_gateway.py
import logging, yaml, time
from datetime import datetime
from typing import Dict, Any, Optional

from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder

logger = logging.getLogger(__name__)

class ModbusGateway:
    """
    - Lee eventos (coils) con debounce y edge:
        * method/proceso -> rising
        * bridge -> toggle (incluye value)
      Si 'proceso' sube (p.ej. send_data), lee todos los 'data' (holding) y arma payload.

    - Escribe estados (holdings) por robot con diff y confirm opcional.
    """
    def __init__(self, config_path="config.yaml", kafka_producer=None, kafka_topic="orders.to_robots"):
        cfg = self._load_cfg(config_path)
        self.mb = cfg["modbus"]
        self.conf = cfg["opc_nodes"]
        self.unit_id = int(self.mb.get("unit_id", 1))
        self.kafka_producer = kafka_producer
        self.kafka_topic = kafka_topic

        # Endianness (MAYÚSCULAS y mapping word_order)
        self.byte_endian = Endian.BIG if self.mb.get("byte_order", "big").upper() == "BIG" else Endian.LITTLE
        self.word_endian = Endian.BIG if self.mb.get("word_order", "high_low").lower() == "high_low" else Endian.LITTLE

        self.client = self._connect()
        self.prev_triggers: Dict[str, bool] = {}
        self.debounce_state: Dict[str, dict] = {}
        self.values_cache: Dict[str, Any] = {}
        self.last_written: Dict[str, Dict[str, Any]] = {}  # {robot_key:{key:val}}

    # ---------- setup ----------
    def _load_cfg(self, path):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _connect(self):
        mode = self.mb.get("mode","tcp").lower()
        if mode == "tcp":
            c = ModbusTcpClient(self.mb["host"], port=int(self.mb.get("port",5020)))
        else:
            c = ModbusSerialClient(method="rtu",
                                   port=self.mb.get("port","/dev/ttyUSB0"),
                                   baudrate=int(self.mb.get("baudrate",115200)),
                                   parity=self.mb.get("parity","N"),
                                   stopbits=int(self.mb.get("stopbits",1)),
                                   bytesize=int(self.mb.get("bytesize",8)),
                                   timeout=2)
        if not c.connect():
            raise RuntimeError("No se pudo conectar a Modbus")
        return c

    def disconnect(self):
        try: self.client.close()
        except: pass

    # ---------- codec ----------
    def _decode_regs(self, regs, dtype):
        # 16-bit: sin decoder para evitar swaps
        if dtype == "uint16":
            return regs[0] & 0xFFFF
        if dtype == "int16":
            v = regs[0] & 0xFFFF
            return v - 0x10000 if (v & 0x8000) else v

        # 32-bit / float32: con decoder respetando endianness
        d = BinaryPayloadDecoder.fromRegisters(regs, byteorder=self.byte_endian, wordorder=self.word_endian)
        if dtype == "uint32":  return d.decode_32bit_uint()
        if dtype == "int32":   return d.decode_32bit_int()
        if dtype == "float32": return d.decode_32bit_float()
        raise ValueError(f"dtype no soportado: {dtype}")

    def _encode_value(self, val, dtype):
        # 16-bit: directo
        if dtype == "uint16":
            return [int(val) & 0xFFFF]
        if dtype == "int16":
            v = int(val)
            if not -32768 <= v <= 32767:
                raise ValueError("int16 fuera de rango")
            return [v & 0xFFFF]

        # 32-bit / float32: builder con endianness
        b = BinaryPayloadBuilder(byteorder=self.byte_endian, wordorder=self.word_endian)
        if dtype == "uint32":   b.add_32bit_uint(int(val))
        elif dtype == "int32":  b.add_32bit_int(int(val))
        elif dtype == "float32":b.add_32bit_float(float(val))
        else: raise ValueError(f"dtype no soportado: {dtype}")
        return b.to_registers()

    def _write_point(self, entry: Dict[str, Any], value):
        if entry.get("kind","holding") != "holding":
            raise ValueError("Solo holdings en write")
        addr = int(entry["addr"])
        dtype = entry.get("dtype","uint16")
        regs  = self._encode_value(value, dtype)
        fc    = int(entry.get("fc", 6 if len(regs)==1 else 16))

        if fc == 6 and len(regs) == 1:
            rr = self.client.write_register(address=addr, value=regs[0], slave=self.unit_id)
        else:
            rr = self.client.write_registers(address=addr, values=regs, slave=self.unit_id)
        if rr.isError():
            raise RuntimeError(rr)

    def _confirm_point(self, entry: Dict[str, Any], expected) -> bool:
        addr = int(entry["addr"])
        dtype = entry.get("dtype","uint16")
        ln = 2 if dtype in ("uint32","int32","float32") else 1
        rr = self.client.read_holding_registers(address=addr, count=ln, slave=self.unit_id)
        if rr.isError():
            return False
        val = self._decode_regs(rr.registers, dtype)
        try:
            return float(val) == float(expected)
        except:
            return val == expected

    def _edge_kind(self, t: str):
        if t in ("method","proceso"): return "rising"
        if t == "bridge":             return "toggle"
        return "level"

    # ---------- events (poll de READ/coils) ----------
    def poll_events_once(self):
        """Lee coils (READ) con debounce y dispara eventos a Kafka.
           Si 'proceso' sube, lee todos los DATA (holdings) y los incluye en params."""
        for name, item in self.conf.get("read", {}).items():
            mb = item.get("modbus", {})
            if mb.get("kind") != "coil":
                continue
            addr = int(mb["addr"])
            fc = int(mb.get("fc",1))
            rr = (self.client.read_coils(address=addr, count=1, slave=self.unit_id)
                  if fc==1 else
                  self.client.read_discrete_inputs(address=addr, count=1, slave=self.unit_id))
            if rr.isError():
                logger.warning(f"Lectura coil {name}@{addr} error: {rr}")
                continue
            raw = bool(rr.bits[0])
            val = self._apply_debounce(name, item, raw)
            if val is not None:
                self._handle_event(name, item, val)

    def _apply_debounce(self, name, item, raw_bool) -> Optional[bool]:
        deb_ms = int(item.get("debounce_ms", 0))
        if deb_ms <= 0:
            prev = self.prev_triggers.get(f"stable:{name}", None)
            if prev is None or prev != raw_bool:
                self.prev_triggers[f"stable:{name}"] = raw_bool
                return raw_bool
            return None
        st = self.debounce_state.get(name, {"stable": raw_bool, "last_raw": raw_bool, "t_last": time.monotonic(), "deb": deb_ms/1000.0})
        now = time.monotonic()
        if raw_bool != st["last_raw"]:
            st["last_raw"] = raw_bool
            st["t_last"] = now
        if raw_bool != st["stable"] and (now - st["t_last"]) >= st["deb"]:
            st["stable"] = raw_bool
            self.debounce_state[name] = st
            self.prev_triggers[f"stable:{name}"] = raw_bool
            return raw_bool
        self.debounce_state[name] = st
        return None

    def _handle_event(self, name, cfg, val_bool):
        t = cfg["type"]
        edge = self._edge_kind(t)
        prev = bool(self.prev_triggers.get(name, False))
        fire, payload_val = False, None

        if edge == "rising" and (not prev) and val_bool:
            fire = True
        elif edge == "toggle" and (prev != val_bool):
            fire, payload_val = True, val_bool

        self.prev_triggers[name] = val_bool
        if not fire:
            return

        ts = datetime.now().strftime('%Y%m%dT%H%M%SZ')
        if t == "proceso":
            data = self._read_all_data_holdings()
            self.values_cache.update(data)
            params = dict(data)
        elif t == "bridge":
            params = dict(cfg.get("param", {}))
            params["value"] = bool(payload_val)
            t = "method"
        else:
            params = {}

        payload = {
            "order_id": f"ORD_{ts}_borunte",
            "type": t,
            "name": cfg.get("name", name),
            "params": params,
            "timestamp": ts
        }
        logger.info(f"📦 Evento: {payload}")
        if self.kafka_producer:
            try:
                self.kafka_producer.send(self.kafka_topic, value=payload)
            except Exception as e:
                logger.warning(f"Kafka error: {e}")

    def _read_all_data_holdings(self) -> Dict[str, Any]:
        out = {}
        for name, item in self.conf.get("read", {}).items():
            if item.get("type") != "data":
                continue
            mb = item["modbus"]
            addr, ln = int(mb["addr"]), int(mb.get("length",1))
            dtype, fc = mb.get("dtype","uint16"), int(mb.get("fc",3))
            rr = (self.client.read_holding_registers(address=addr, count=ln, slave=self.unit_id)
                  if fc==3 else
                  self.client.read_input_registers(address=addr, count=ln, slave=self.unit_id))
            if rr.isError():
                logger.warning(f"Lectura data {name}@{addr} error: {rr}")
                continue
            regs = rr.registers
            val = self._decode_regs(regs, dtype) if (ln>1 or dtype!="uint16") else regs[0]
            out[name] = val
        return out

    # ---------- writes (desde Redis) ----------
    def write_status_diff(self, robot_key: str, status: Dict[str, Any], confirm=True):
        """Escribe SOLO cambios en opc_nodes.write[robot_key]."""
        write_map = self.conf.get("write", {}).get(robot_key, {})
        if not write_map:
            logger.warning(f"{robot_key} no definido en YAML")
            return

        last = self.last_written.setdefault(robot_key, {})
        changed: Dict[str, Any] = {}
        for k, v in status.items():
            if k in write_map and last.get(k) != v:
                changed[k] = v

        for k, v in changed.items():
            entry = write_map[k]
            try:
                self._write_point(entry, v)
                ok = True
                if confirm:
                    ok = self._confirm_point(entry, v)
                if ok:
                    last[k] = v
                    logger.info(f"✅ {robot_key}.{k} -> {v}")
                else:
                    logger.warning(f"⚠️ confirm {robot_key}.{k} != {v}")
            except Exception as e:
                logger.warning(f"⚠️ write {robot_key}.{k}@{entry.get('addr')} error: {e}")
