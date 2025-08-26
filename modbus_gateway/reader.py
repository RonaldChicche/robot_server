# read_robot1_once.py
from pymodbus.client import ModbusTcpClient
from datetime import datetime

client = ModbusTcpClient("127.0.0.1", port=5020)
client.connect()

def ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

# Mapa de señales robot1
# robot1 = {
#     "state_green":     { "fc": 6, "addr": 100 },
#     "state_yellow":    { "fc": 6, "addr": 101 },
#     "state_red":       { "fc": 6, "addr": 102 },
#     "running":         { "fc": 6, "addr": 103 },
#     "terminado":       { "fc": 6, "addr": 104 },
#     "set_ok":          { "fc": 6, "addr": 105 },
#     "stack_count":     { "fc": 6, "addr": 106 },
#     "stack_ready":     { "fc": 6, "addr": 107 },
#     "layer_ready":     { "fc": 6, "addr": 108 },
#     "gripper_state":   { "fc": 6, "addr": 109 },
#     "alarm_code":      { "fc": 6, "addr": 110 },
# }

robot1 = {
    "pos_x": { "addr": 150 },
    "pos_y": { "addr": 151 },
    "pos_z": { "addr": 152 },
    "ang_u": { "addr": 153 },
    "ang_v": { "addr": 154 },
    "ang_w": { "addr": 155 },
    "j1":     { "addr": 156 },
    "j2":     { "addr": 157 },
    "j3":     { "addr": 158 },
    "j4":     { "addr": 159 },
    "j5":     { "addr": 160 },
    "j6":     { "addr": 161 },
}

def read_register(addr):
    r = client.read_holding_registers(addr, count=1)
    return r.registers[0] if not r.isError() else "ERR"

# Lectura única
print(f"[{ts()}] Lectura única de robot1:")
for name, cfg in robot1.items():
    value = read_register(cfg["addr"])
    print(f"  {name}: {value}")

client.close()
