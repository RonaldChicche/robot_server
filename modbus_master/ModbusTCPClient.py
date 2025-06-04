from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

import json

class ModbusTCPClient:
    def __init__(self, ip='127.0.0.1', port=502):
        self.client = ModbusTcpClient(ip, port=port)
        self.connected = False

    def connect(self):
        self.connected = self.client.connect()
        return self.connected

    def close(self):
        self.client.close()
        self.connected = False

    def read_holding_registers(self, address, count=1):
        try:
            result = self.client.read_holding_registers(address=address, count=count)
            if not result.isError():
                return result.registers
            else:
                print(f"❌ Error leyendo registros en {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return None

    def write_single_register(self, address, value):
        try:
            result = self.client.write_register(address=address, value=value)
            if not result.isError():
                return True
            else:
                print(f"❌ Error escribiendo en registro {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return False

    def write_multiple_registers(self, address, values):
        try:
            result = self.client.write_registers(address=address, values=values)
            if not result.isError():
                return True
            else:
                print(f"❌ Error escribiendo múltiples registros desde {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return False

    def write_coils(self, address, values):
        try:
            result = self.client.write_coils(address=address, values=values)
            if not result.isError():
                return True
            else:
                print(f"❌ Error escribiendo coils desde {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return False
    
    def read_coils(self, address, count=1):
        try:
            result = self.client.read_coils(address=address, count=count)
            if not result.isError():
                return result.bits
            else:
                print(f"❌ Error leyendo coils en {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return None
    
    def read_discrete_inputs(self, address, count=1):
        try:
            result = self.client.read_discrete_inputs(address=address, count=count)
            if not result.isError():
                return result.bits
            else:
                print(f"❌ Error leyendo inputs en {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return None
    
    def read_input_registers(self, address, count=1):
        try:
            result = self.client.read_input_registers(address=address, count=count)
            if not result.isError():
                return result.registers
            else:
                print(f"❌ Error leyendo inputs en {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return None
    
    def read_holding_registers(self, address, count=1):
        try:
            result = self.client.read_holding_registers(address=address, count=count)
            if not result.isError():
                return result.registers
            else:
                print(f"❌ Error leyendo inputs en {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return None



class ModbusDictionaryClient:
    def __init__(self, ip, port, json_path, slave=1):
        self.client = ModbusTcpClient(ip, port=port)
        self.slave = slave
        with open(json_path, 'r', encoding='utf-8') as f:
            self.registers = {item["key"]: item for item in json.load(f)}

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def read(self, key):
        reg = self.registers.get(key)
        if not reg or "R" not in reg["access"]:
            raise ValueError(f"No se puede leer el registro '{key}'")

        address = reg["address"]
        count = reg["size"]
        if reg["function"] == 3:
            result = self.client.read_holding_registers(address=address, count=count, slave=self.slave)
        else:
            raise NotImplementedError("Función no soportada aún")

        if result.isError():
            raise IOError(f"Error al leer {key}: {result}")
        return result.registers if count > 1 else result.registers[0]
