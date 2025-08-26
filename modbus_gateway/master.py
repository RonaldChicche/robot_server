# client_agresivo.py
from pymodbus.client import ModbusTcpClient
import random
import time
from datetime import datetime

client = ModbusTcpClient("190.168.10.108", port=5020)
client.connect()

unit = 1
MAX_ADDR = 400
BLOCK_SIZE = 125

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def read_all_registers(client, unit=1):
    all_data = []
    for addr in range(0, MAX_ADDR, BLOCK_SIZE):
        count = min(BLOCK_SIZE, MAX_ADDR - addr)
        r = client.read_holding_registers(addr, count=count)
        if not r.isError():
            all_data.extend(r.registers)
        else:
            print(f"Error leyendo desde {addr} count={count}")
    return all_data

try:
    while True:
        t0 = time.time()

        # Escritura aleatoria
        addr_w = random.randint(0, MAX_ADDR - 1)
        value_w = random.randint(0, 65535)
        client.write_register(addr_w, value_w)

        # Lectura completa
        data = read_all_registers(client)
        
        t1 = time.time()

        print(f"[{timestamp()}] Δt={(t1 - t0)*1000:.2f} ms | W: addr={addr_w}, val={value_w} | Leídos {len(data)} registros. R[0]={data[0]}")

        time.sleep(0.1)  # Ajusta la agresividad aquí

except KeyboardInterrupt:
    print(f"[{timestamp()}] Cliente detenido por usuario.")
    client.close()
