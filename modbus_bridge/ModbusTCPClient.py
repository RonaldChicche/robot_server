from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

import re
import json
import struct

class ModbusTCPClient:
    def __init__(self, ip='127.0.0.1', port=502, name="1"):
        self.client = ModbusTcpClient(ip, port=port, name=name)
        self.connected = False

    def connect(self):
        self.connected = self.client.connect()
        return self.connected

    def close(self):
        self.client.close()
        self.connected = False

    def read_modbus_values(self, start_address, length, double_bit=False):
        """
        Lee valores Modbus desde una dirección y los interpreta como int16 o float32.

        Args:
            start_address (int): Dirección inicial.
            length (int): Cantidad total de registros a leer (según JSON).
            double_bit (bool): True para float32 (2 registros), False para int16 (1 registro).

        Returns:
            list of float or int, o None si hay error.
        """
        try:
            rr = self.client.read_holding_registers(address=start_address, count=length)
            if rr.isError():
                print("❌ Error en lectura Modbus")
                return None

            values = []

            if double_bit:
                # Asegúrate de que hay múltiplos de 2 registros
                for i in range(0, len(rr.registers), 2):
                    raw = (rr.registers[i] << 16) + rr.registers[i + 1]
                    val = struct.unpack('>f', raw.to_bytes(4, byteorder='big'))[0]
                    values.append(val)
            else:
                # Cada registro es un int16
                values = rr.registers

            return values

        except Exception as e:
            print(f"⚠️ Error: {e}")
            return None
    
    def read_modbus_scaled_ints(self, start_address, count):
        """
        Lee múltiples valores int32 desde Modbus y los escala (útil para milésimas).
        
        Args:
            start_address (int): dirección inicial Modbus.
            count (int): cantidad de enteros a leer.

        Returns:
            list of float: valores escalados, o None si falla.
        """
        try:
            rr = self.client.read_holding_registers(address=start_address, count=count * 2)
            if rr.isError():
                print("❌ Error en lectura Modbus")
                return None

            values = []
            for i in range(count):
                hi = rr.registers[i * 2]
                lo = rr.registers[i * 2 + 1]
                raw = struct.pack('>HH', hi, lo)
                value = struct.unpack('>i', raw)[0]  # entero con signo
                values.append(value)
            return values

        except Exception as e:
            print(f"⚠️ Error: {e}")
            return None

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

    def write_coil(self, address: int, value: bool):
        try:
            result = self.client.write_coil(address=address, value=value)
            if not result.isError():
                return True
            else:
                print(f"❌ Error escribiendo coil desde {address}")
        except ModbusIOException as e:
            print(f"⚠️ IO Error: {e}")
        return False

    def write_coils(self, address: int, values: list):
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


class ModbusBorunteClient(ModbusTCPClient):
    def __init__(self, ip='127.0.0.1', port=502, name="1"):
        super().__init__(ip, port, name)
        self.load_config()

    def load_config(self):
        json_coils = "config/diccionario_coils.json"
        json_registers = "config/diccionario_registros.json"
        try:
            with open(json_coils, "r") as f:
                self.coils = json.load(f)
            with open(json_registers, "r") as f:
                self.registers = json.load(f)
        except FileNotFoundError as e:
            print("No se encontraron los archivos de configuración ->", e)

    def start_button(self):
        # write 1 in the register start_button
        return self.send_command("start_button", 1)
    
    def stop_button(self):
        # write 1 in the register stop_button
        return self.send_command("stop_button", 1)
    
    def force_stop(self):
        # write 1 in the register force_stop
        return self.send_command("force_stop", 1)
    
    def clear_alarm(self):
        # write 1 in the register clear_alarm
        return self.send_command("clear_alarm", 1)
    
    def modify_global_velocity(self, value):   # -------------------- Verificar
        """
        Escribe un valor entero de 0 a 1000 a la dirección 20200.
        """
        if not (0 <= value <= 1000):
            raise ValueError("⚠️ Valor fuera de rango (0–1000)")
        
        address = self.registers["machine_status"]["global_velocity"]["address"]
        
        return self.write_single_register(address, value)

    def read_global_velocity(self):
        """
        Lee un registro Modbus y lo interpreta como int16 o float32.
        """
        address = self.registers["machine_status"]["global_velocity"]["address"]
        length = self.registers["machine_status"]["global_velocity"]["length"]
        double_bit = self.registers["machine_status"]["global_velocity"]["double_bit"]
        return self.read_modbus_values(address, length, double_bit)
    
    def write_output(self, coil_name: str, value: bool):
        """
        Escribe un valor booleano a la direccion correspondiente.
        Args:
            coil_name (str): Nombre del coil a escribir (ej: "Y010").
            value (bool): Valor booleano a escribir.
        Returns:
            bool: True si la escritura fue exitosa, False en caso contrario.
        """
        coil = coil_name.lower()
        key = ''.join(re.findall(r'[A-Za-z]', coil))
        address = self.coils[key]["addresses"][coil]
        return self.write_coil(address, value)

    def read_output(self, coil_name: str):
        """
        Lee un valor booleano a la direccion correspondiente.
        Args:
            coil_name (str): Nombre del coil a leer (ej: "Y010").
        Returns:
            bool: Valor booleano leido.
        """
        coil = coil_name.lower()
        key = ''.join(re.findall(r'[A-Za-z]', coil))
        address = self.coils[key]["address"]
        return self.read_coils(address)
    
    def read_all_outputs(self):
        """
        Lee todos los valores booleanos de los coils.
        Returns:
            dict: Diccionario con los nombres de los coils como claves y los valores booleanos como valores.
        """
        result = {}
        for name in self.coils.keys():
            mem_addr = list(self.coils[name]["addresses"].keys())
            start_address = self.coils[name]["addresses"][mem_addr[0]]
            count = len(mem_addr)
            values = self.read_coils(start_address, count)
            sub_result = dict(zip(mem_addr, values))
            result[name] = sub_result
        return result

    def send_command(self, register_name, value):
        """
        Envia un comando con el nombre correspondiente activandolo con un 1
        Args:
            register_name (str): Nombre del registro a escribir (ej: "start_button").
            value (int): Valor entero a escribir. (ej: 1)
        Returns:
            bool: True si la escritura fue exitosa, False en caso contrario.
        """
        address = self.registers["command"][register_name]["address"]
        return self.write_single_register(address, value)
    
    def read_status(self, register_name):
        """
        Lee un registro Modbus y lo interpreta como int16 o float32.
        Args:
            register_name (str): Nombre del registro a leer (ej: "global_velocity").
        Returns:
            list of float or int, o None si hay error.
        """
        address = self.registers["machine_status"][register_name]["address"]
        length = self.registers["machine_status"][register_name]["length"]
        double_bit = self.registers["machine_status"][register_name]["double_bit"]
        return self.read_modbus_values(address, length, double_bit)
    
    def read_all_status(self):
        """
        Lee todos los registros Modbus y los interpreta como int16 o float32.
        Returns:
            dict: Diccionario con los nombres de los registros como claves y los valores como valores.
        """
        result = {}
        for name in self.registers["machine_status"]:
            value = self.read_status(name)
            result[name] = value
        return result
        
    def read_memory_address(self, address_number: int, number_of_addresses: int):
        """
        Lee múltiples valores int32 desde Modbus y los escala (útil para milésimas).
        
        Args:
            address_number (int): dirección inicial Modbus (800 - 890)
            count (int): cantidad de enteros a leer

        Returns:
            Diccionario con los addresses y sus valores {'801': value, ...}
        """
        base_modbus = self.registers["address"]["800"]
        # verifica que address_number este entre 800 y 890 y que el ultimo address tambien lo este
        if address_number < 800 or address_number > 890 or address_number + number_of_addresses - 1 > 890 or number_of_addresses < 1:
            raise ValueError("⚠️ Direccion fuera de rango (tiene que estar entre 800 y 890) o la cantidad de addresses es menor a 1")
        
        start_address = base_modbus + (address_number - 800) * 2
        values = self.read_modbus_scaled_ints(start_address, number_of_addresses)
        # creacion de diccionario
        logical_keys = [str(800 + i) for i in range(number_of_addresses)]
        return dict(zip(logical_keys, values))

    def write_memory_address(self, address_number: int, value: list):
        """
        Escribe múltiples valores int32 desde Modbus y los escala (útil para milésimas).
        
        Args:
            address_number (int): direccion inicial Modbus (800 - 890)
            value (list): lista de enteros a escribir

        Returns:
            bool: True si la escritura fue exitosa, False en caso contrario.
        """
        if address_number < 800 or address_number > 890 or address_number + len(value) - 1 > 890 or len(value) < 1:
            raise ValueError("⚠️ Direccion fuera de rango (tiene que estar entre 800 y 890) o la cantidad de valores es menor a 1")
        
        base_modbus = self.registers["address"]["800"]
        registros_modbus = []
        for val in value:
            high, low = struct.unpack('>HH', struct.pack('>i', val))
            registros_modbus.extend([high, low])

        start_address = base_modbus + (address_number - 800) * 2
        return self.write_multiple_registers(start_address, registros_modbus)