from pymodbus.client import ModbusTcpClient
import logging

# Configuración básica
IP = "192.168.5.77"  # IP del PLC
PORT = 5020
ADDR = 39  # Dirección del holding register compartido

bits_to_modify = {
    "start_button": (0, False),
    "pause_button": (2, False),
    "stop_button": (1, False),
    "clear_alarm_button": (3, False),
    "bit_stack": (4, False),
    "resume_button": (10, False),
    "send_data": (9, False),
    "test": (5, False),
    "jog_z": (6, False),
    "home": (7, False),
    "gripper_off": (8, False),
}

def modify_bits(client, addr, bit_map):
    rr = client.read_holding_registers(addr, count=1)
    if rr.isError():
        logging.error("❌ Error al leer el registro")
        return

    original = rr.registers[0]
    modified = original

    for name, (bit, value) in bit_map.items():
        mask = 1 << bit
        if value:
            modified |= mask
        else:
            modified &= ~mask
        logging.info(f"🔧 {name}: bit {bit} → {'1' if value else '0'}")

    if modified != original:
        rq = client.write_register(addr, modified)
        if rq.isError():
            logging.error("❌ Error al escribir el registro")
        else:
            logging.info(f"✅ Registro {addr} modificado: {bin(original)} → {bin(modified)}")
    else:
        logging.info("⏭️ No hubo cambios en el registro")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = ModbusTcpClient(IP, port=PORT)
    if client.connect():
        modify_bits(client, ADDR, bits_to_modify)
        client.close()
    else:
        logging.error("❌ No se pudo conectar al PLC")
