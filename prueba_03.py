from pymodbus.client import ModbusTcpClient
import struct
import logging

IP = "192.168.5.77"
PORT = 5020
UNIT_ID = 1

def write_float32(client, addr, value):
    # Empaqueta el float en 2 registros Modbus (big endian)
    packed = struct.pack(">f", value)
    registers = struct.unpack(">HH", packed)
    rq = client.write_registers(addr, registers)
    if rq.isError():
        logging.error(f"❌ Error al escribir float32 en {addr}")
    else:
        logging.info(f"✅ float32 {value} → addr {addr} ({registers})")

def write_int16(client, addr, value):
    rq = client.write_register(addr, value)
    if rq.isError():
        logging.error(f"❌ Error al escribir int16 en {addr}")
    else:
        logging.info(f"✅ int16 {value} → addr {addr}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = ModbusTcpClient(IP, port=PORT)
    if client.connect():
        # Ejemplos de escritura
        write_float32(client, 40, 101.6)     # ancho_barra
        write_float32(client, 42, 3658.0)    # long_barra
        write_float32(client, 44, 6.35)      # espesor
        write_int16(client, 55, 4)           # cantidad_x
        write_int16(client, 57, 2)           # no_carro
        client.close()
    else:
        logging.error("❌ No se pudo conectar al PLC")
