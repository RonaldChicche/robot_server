import time, yaml, logging, json
from datetime import datetime
from typing import Dict, Any, Optional

from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian

logger = logging.getLogger(__name__)

class ModbusGateway(ModbusTcpClient):
    """
    Gateway Modbus basado en YAML:
    - Lee eventos (READ) con debounce y edge:
        * type=method/proceso -> rising
        * type=bridge         -> toggle (incluye value)
      Si 'proceso' sube (send_data), lee todos los type=data y los adjunta al payload.

    - Escribe estados (WRITE) por robot con diff + confirm opcional.
      Soporta holdings tipados y bits (R/M/W de words STW/CTW).
    
    - Usa convert_to_registers / convert_from_registers (sin BinaryPayload*).
    """
    def __init__(self,modbus_host="127.0.0.1", modbus_port=5020, config_path="config.yaml", kafka_producer=None, kafka_topic="orders.to_robots"):
        # ---- Cargar YAML ----
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        mb = cfg["modbus"]
        self.conf = cfg["opc_nodes"]
        self.unit_id = int(mb.get("unit_id", 1))

        # ---- Endianness (respeta YAML: byte_order BIG/LITTLE, word_order high_low/low_high) ----
        self.byte_endian = Endian.BIG if str(mb.get("byte_order","BIG")).upper()=="BIG" else Endian.LITTLE
        self.word_endian = Endian.BIG if str(mb.get("word_order","high_low")).lower()=="high_low" else Endian.LITTLE

        # ---- Cliente (TCP o Serial-RTU) ----
        mode = str(mb.get("mode","tcp")).lower()
        if mode == "tcp":
            super().__init__(host=modbus_host, port=modbus_port, name="MB-Gateway")
        else:
            raise RuntimeError("Solo TCP en esta clase. (RTU: crear variante específica)")

        if not self.connect():
            raise RuntimeError("No se pudo conectar a Modbus")

        # ---- Kafka opcional ----
        self.kafka_producer = kafka_producer
        self.kafka_topic = kafka_topic

        # ---- Estados internos ----
        self.prev_triggers: Dict[str, bool] = {}   # último estado estable de cada evento
        self.debounce_state: Dict[str, dict] = {}  # filtros de debounce
        self.values_cache: Dict[str, Any] = {}     # cache de lecturas 'data'
        self.last_written: Dict[str, Dict[str, Any]] = {}  # {robot_key:{key:val}}

        self._event_groups = self._build_event_groups()
        self._proceso_entry = self._find_proceso_entry()  # ('send_data', cfg) o (None, None)

        logger.info(f"🟢 ModbusGateway iniciado ...")


    # ===================== Helpers =====================
    @staticmethod
    def _ts():
        return datetime.now().strftime('%Y%m%dT%H%M%SZ')

    def _dtype_token(self, dtype: str):
        """Mapea cadena YAML -> token DATATYPE de pymodbus.convert_*."""
        m = {
            "uint16":  self.DATATYPE.UINT16,
            "int16":   self.DATATYPE.INT16,
            "uint32":  self.DATATYPE.UINT32,
            "int32":   self.DATATYPE.INT32,
            "float32": self.DATATYPE.FLOAT32,
            "float64": self.DATATYPE.FLOAT64,
            "int64":   self.DATATYPE.INT64,
            "uint64":  self.DATATYPE.UINT64,
        }
        if dtype not in m:
            raise ValueError(f"dtype no soportado: {dtype}")
        return m[dtype]

    @staticmethod
    def _dtype_len(dtype: str) -> int:
        return 2 if dtype in ("uint32","int32","float32","uint64","int64","float64") else 1

    @staticmethod
    def _get_bit(word: int, bit: int) -> int:
        return 1 if (word >> bit) & 1 else 0

    @staticmethod
    def _set_bit(word: int, bit: int, value: bool) -> int:
        mask = 1 << bit
        return (word | mask) if value else (word & ~mask)

    @staticmethod
    def _edge_kind(t: str):
        if t in ("method","proceso"): return "rising"
        if t == "bridge":             return "toggle"
        return "level"

    # ===================== Codec =====================
    def _decode_regs(self, regs, dtype: str):
        return self.convert_from_registers(
            regs, self._dtype_token(dtype), word_order=self.word_endian
        )

    def _encode_value(self, val, dtype: str):
        return self.convert_to_registers(
            val, self._dtype_token(dtype), word_order=self.word_endian
        )
    
    def _build_event_groups(self):
        groups = {}
        for name, item in self.conf.get("read", {}).items():
            t = item.get("type")
            if t not in ("method", "proceso", "bridge"):
                continue
            mb = item.get("modbus", {})
            if mb.get("kind") == "holding" and "bit" in mb:
                addr = int(mb["addr"])
                bit  = int(mb["bit"])
                groups.setdefault(addr, []).append((name, item, bit))
        return groups
    
    def _find_proceso_entry(self):
        for k, item in self.conf.get("read", {}).items():
            if item.get("type") == "proceso":
                return k, item
        return None, None

    def _emit_send_data(self, params: dict):
        name, cfg = self._proceso_entry
        t  = "proceso"
        nm = (cfg.get("name", name) if cfg else "send_data")
        ts = self._ts()
        payload = {
            "order_id": f"ORD_{ts}_borunte",
            "type": t,
            "name": nm,
            "params": params,
            "timestamp": ts
        }
        logger.info(f"📦 Auto send_data (by data change): {payload}")
        if self.kafka_producer:
            try:
                self.kafka_producer.send(self.kafka_topic, value=payload)
            except Exception as e:
                logger.warning(f"Kafka error: {e}")

    # ===================== Lectura DATA =====================
    def _auto_send_data_on_change(self, float_eps: float = 1e-4):
        """
        Lee todos los 'data' holdings y, si cualquiera cambia vs cache,
        emite un evento 'proceso' (send_data) con TODOS los datos actuales.
        La primera lectura solo inicializa cache (no dispara).
        """
        current = self._read_all_data_holdings()
        #logger.info(f"📦 Lectura DATA: {current}")
        if not self.values_cache:
            self.values_cache = dict(current)  # primera muestra: NO dispara
            return

        changed = False
        for k, new in current.items():
            old = self.values_cache.get(k)
            if old is None:
                changed = True
                break
            try:
                # tolerancia para float32
                if isinstance(new, float) or isinstance(old, float):
                    if abs(float(new) - float(old)) > float_eps:
                        changed = True
                        break
                else:
                    if new != old:
                        changed = True
                        break
            except Exception:
                if new != old:
                    changed = True
                    break

        if changed:
            self._emit_send_data(current)

        self.values_cache = dict(current)  # actualiza cache siempre

    def _read_all_data_holdings(self) -> Dict[str, Any]:
        out = {}
        for name, item in self.conf.get("read", {}).items():
            if item.get("type") != "data":
                continue
            mb = item["modbus"]
            addr   = int(mb["addr"])
            dtype  = mb.get("dtype","uint16")
            length = int(mb.get("length", self._dtype_len(dtype)))
            fc     = int(mb.get("fc", 3))
            if fc == 3:
                rr = self.read_holding_registers(address=addr, count=length, slave=self.unit_id)
            else:
                rr = self.read_input_registers(address=addr, count=length, slave=self.unit_id)
            if rr.isError():
                logger.warning(f"Lectura data {name}@{addr} error: {rr}")
                continue
            out[name] = self._decode_regs(rr.registers, dtype)
        return out

    # ===================== Eventos (READ) =====================
    def poll_events_once(self):
        """Lee CTW (word) una vez por dirección y dispara solo en rising (method/proceso) o toggle (bridge).
        La PRIMERA lectura solo inicializa prev y NO dispara."""
        # 1) CTW por grupos (holding+bit)
        for addr, items in self._event_groups.items():
            rr = self.read_holding_registers(address=addr, count=1, slave=self.unit_id)
            if rr.isError():
                logger.warning(f"Lectura CTW@{addr} error: {rr}")
                continue
            word = rr.registers[0] & 0xFFFF
            #logger.info(f"📦 Lectura CTW@{addr}: {word:04X}")
            for i, item in enumerate(items):
                estado = (word >> i) & 1
            #logger.info(f"🔍 CTW@{addr} {item} = {estado} || {self.prev_triggers}")
            for name, cfg, bit in items:
                cur = bool((word >> bit) & 1)
                prev = self.prev_triggers.get(name, None)
                if prev is None:
                    # primera muestra: inicializa y no dispara
                    self.prev_triggers[name] = cur
                    logger.info(f"🔍 CTW@{addr} {name} = {cur} (primera muestra)")
                    continue
                self._handle_event_simple(name, cfg, prev, cur)
                self.prev_triggers[name] = cur
        
        self._auto_send_data_on_change()

    def _handle_event_simple(self, name, cfg, prev: bool, cur: bool):
        t = cfg.get("type")
        # method/proceso → solo rising (0→1)
        if t in ("method", "proceso"):
            if (not prev) and cur:
                self._emit_event(name, cfg, cur)
            return
        # bridge → toggle (0↔1)
        if t == "bridge" and (prev != cur):
            self._emit_event(name, cfg, cur)

    def _emit_event(self, name, cfg, cur_bool):
        t = cfg["type"]
        ts = datetime.now().strftime('%Y%m%dT%H%M%SZ')

        if t == "proceso":
            params = self._read_all_data_holdings()  # lee DATA al momento del trigger
        elif t == "bridge":
            params = dict(cfg.get("param", {}))
            params["value"] = bool(cur_bool)
            t = "method"  # mismo formato de evento que method
        else:
            params = {}

        payload = {
            "order_id": f"ORD_{ts}_borunte",
            "robot_id": '01',
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


    # ===================== Escritura (WRITE) =====================
    def _write_point(self, entry: Dict[str, Any], value):
        """Escribe un punto: bit en holding o holding tipado completo."""
        addr = int(entry["addr"])
        if "bit" in entry:
            # R/M/W de un word (STW/CTW)
            rd = self.read_holding_registers(address=addr, count=1, slave=self.unit_id)
            if rd.isError(): raise RuntimeError(rd)
            cur = rd.registers[0] & 0xFFFF
            neww = self._set_bit(cur, int(entry["bit"]), bool(value))
            wr = self.write_register(address=addr, value=neww, slave=self.unit_id)
            if wr.isError(): raise RuntimeError(wr)
            return

        dtype = entry.get("dtype","uint16")
        regs = self._encode_value(value, dtype)
        if len(regs) == 1:
            wr = self.write_register(address=addr, value=regs[0], slave=self.unit_id)
        else:
            wr = self.write_registers(address=addr, values=regs, slave=self.unit_id)
        if wr.isError():
            raise RuntimeError(wr)

    def _confirm_point(self, entry: Dict[str, Any], expected) -> bool:
        addr = int(entry["addr"])
        if "bit" in entry:
            rb = self.read_holding_registers(address=addr, count=1, slave=self.unit_id)
            if rb.isError(): return False
            got = self._get_bit(rb.registers[0] & 0xFFFF, int(entry["bit"]))
            return got == (1 if expected else 0)

        dtype = entry.get("dtype","uint16")
        ln = self._dtype_len(dtype)
        rb = self.read_holding_registers(address=addr, count=ln, slave=self.unit_id)
        if rb.isError(): return False
        val = self._decode_regs(rb.registers, dtype)
        if dtype == "float32":
            try: return abs(float(val) - float(expected)) <= 1e-4
            except: return False
        return val == expected

    def write_status_diff(self, robot_key: str, status: Dict[str, Any], confirm: bool = True):
        """Escribe SOLO cambios en opc_nodes.write[robot_key], delega en _write/_confirm."""
        write_map = self.conf.get("write", {}).get(robot_key)
        if not write_map:
            logger.warning(f"{robot_key} no definido en YAML")
            return
        last = self.last_written.setdefault(robot_key, {})
        changed = {k: v for k, v in status.items() if k in write_map and last.get(k) != v}

        for k, v in changed.items():
            entry = write_map[k]
            try:
                self._write_point(entry, v)
                if confirm and not self._confirm_point(entry, v):
                    logger.warning(f"⚠️ confirm {robot_key}.{k}@{entry.get('addr')} != {v}", exc_info=True)
                    continue
                last[k] = v
            except Exception as e:
                logger.warning(f"⚠️ write {robot_key}.{k}@{entry.get('addr')} error: {e}")

    # ===================== Salud / utilidades =====================
    def health_check(self) -> bool:
        try:
            rr = self.read_coils(address=0, count=1, slave=self.unit_id)
            return not rr.isError()
        except Exception:
            return False

    # ===================== (Opcional) una pasada de Redis =====================
    def process_redis_once(self, rd, robot_key: str, status_key: str, process_key: str, confirm=True):
        """
        Toma una muestra desde Redis y:
         1) Escribe estados en WRITE (solo difs).
         2) Mapea process:state → luces (state_green/yellow/red).
         3) Escanea eventos (READ) y lanza a Kafka.
        """
        raw = rd.get(status_key)
        if raw:
            try:
                data = json.loads(raw)
                # ---- adapta tu mapeo a las claves de YAML.write ----
                status: Dict[str, Any] = {}
                s   = data.get("status", {})
                sin = s.get("status", {})
                y   = s.get("outputs", {}).get("y", {})

                status["running"]       = 1 if data.get("movement_status") else 0
                status["terminado"]     = 1 if y.get("y33") else 0
                status["set_ok"]        = 1 if y.get("y45") else 0
                status["stack_ready"]   = 1 if y.get("y35") else 0
                status["layer_ready"]   = 1 if y.get("y36") else 0
                status["gripper_state"] = 1 if y.get("y23") else 0
                status["alarm_code"]    = int((sin.get("alarm_code") or [0])[0])
                cnt = s.get("counters", {})
                status["stack_count"]   = int(cnt.get("counter-2",{}).get("current",0))

                wp = sin.get("world_position",[0,0,0,0,0,0])
                status.update({
                    "pos_x": float(wp[0]), "pos_y": float(wp[1]), "pos_z": float(wp[2]),
                    "ang_u": float(wp[3]), "ang_v": float(wp[4]), "ang_w": float(wp[5]),
                })
                tq = sin.get("axis_torque",[0,0,0,0,0,0])
                for i in range(6):
                    status[f"j{i+1}"] = float(tq[i])

                self.write_status_diff(robot_key, status, confirm=confirm)
            except Exception as e:
                logger.warning(f"redis status parse/write error: {e}")

        ps = rd.get(process_key) or ""
        lights = {
            "state_green":  1 if ps=="Running" else 0,
            "state_yellow": 1 if ps=="Paused"  else 0,
            "state_red":    1 if ps=="Stopped" else 0,
        }
        self.write_status_diff(robot_key, lights, confirm=False)

        # Eventos → Kafka
        self.poll_events_once()
