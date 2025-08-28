# read_robot1_float.py
from pymodbus.client import ModbusTcpClient
from datetime import datetime
import struct

client = ModbusTcpClient("127.0.0.1", port=5020)
client.connect()

def ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

# Nuevo mapa con tipo de dato
robot1 = {
    "pos_x": { "kind": "holding", "addr": 4,  "dtype": "float32" },
    "pos_y": { "kind": "holding", "addr": 6,  "dtype": "float32" },
    "pos_z": { "kind": "holding", "addr": 8,  "dtype": "float32" },
    "ang_u": { "kind": "holding", "addr": 10, "dtype": "float32" },
    "ang_v": { "kind": "holding", "addr": 12, "dtype": "float32" },
    "ang_w": { "kind": "holding", "addr": 14, "dtype": "float32" },
    
    "j1": { "kind": "holding", "addr": 16, "dtype": "float32" },
    "j2": { "kind": "holding", "addr": 18, "dtype": "float32" },
    "j3": { "kind": "holding", "addr": 20, "dtype": "float32" },
    "j4": { "kind": "holding", "addr": 22, "dtype": "float32" },
    "j5": { "kind": "holding", "addr": 24, "dtype": "float32" },
    "j6": { "kind": "holding", "addr": 26, "dtype": "float32" },
}

def read_float32(addr):
    r = client.read_holding_registers(addr, count=2)
    if r.isError():
        return "ERR"
    # Combina los dos registros en bytes (big-endian por defecto Modbus)
    raw = struct.pack(">HH", r.registers[0], r.registers[1])
    return round(struct.unpack(">f", raw)[0], 4)  # Precisión ajustable

# Lectura única
print(f"[{ts()}] Lectura única de robot1 (float32):")
for name, cfg in robot1.items():
    if cfg["dtype"] == "float32":
        value = read_float32(cfg["addr"])
        print(f"  {name}: {value}")

client.close()
