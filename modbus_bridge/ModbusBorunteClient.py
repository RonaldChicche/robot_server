from pymodbus.client import ModbusTcpClient

import re
import json
import struct
import logging

logger = logging.getLogger("ModbusBorunteClient")

class ModbusBorunteError(Exception): pass

class ModbusBorunteClient(ModbusTcpClient):
    def __init__(self, host='127.0.0.1', port=502, name="1", **kwargs):
        super().__init__(host, port=port, name=name, **kwargs)
        self.load_config()

    def load_config(self):
        json_coils = "config/diccionario_coils.json"
        json_registers = "config/diccionario_registros.json"
        try:
            with open(json_coils, "r") as f:
                self.coils = json.load(f)
            with open(json_registers, "r") as f:
                self.registers = json.load(f)
            logger.info("Archivos de configuración cargados correctamente.")
        except FileNotFoundError as e:
            logger.error(f"No se encontraron los archivos de configuración: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error de formato en JSON: {e}")
            raise

    def health_check(self):
        try:
            rr = self.read_coils(0, 1)
            return rr.isError() is False
        except Exception as e:
            return False
        
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
        rr = self.read_holding_registers(address=start_address, count=length)
        if rr.isError():
            raise ModbusBorunteError("Lectura Modbus fallida o respuesta inválida")

        values = []

        if double_bit:
            if len(rr.registers) % 2 != 0:
                raise ModbusBorunteError(f"Cantidad de registros no válida para float32: {len(rr.registers)}")

            for i in range(0, len(rr.registers), 2):
                raw = (rr.registers[i] << 16) + rr.registers[i + 1]
                val = struct.unpack('>f', raw.to_bytes(4, byteorder='big'))[0]
                values.append(val)
        else:
            values = rr.registers

        return values
    
    def read_modbus_scaled_ints(self, start_address, count):
        """
        Lee múltiples valores int32 desde Modbus y los escala (útil para milésimas).
        
        Args:
            start_address (int): dirección inicial Modbus.
            count (int): cantidad de enteros a leer.

        Returns:
            list of float: valores escalados, o None si falla.
        """
        rr = self.read_holding_registers(address=start_address, count=count * 2)
        if rr.isError():
            raise ModbusBorunteError("Lectura Modbus fallida o respuesta inválida")

        values = []
        for i in range(count):
            hi = rr.registers[i * 2]
            lo = rr.registers[i * 2 + 1]
            raw = struct.pack('>HH', hi, lo)
            value = struct.unpack('>i', raw)[0]  # entero con signo
            values.append(value)

        return values
    
    def read_output(self, coil_name: str):
        """
        Lee un valor booleano a la direccion correspondiente.
        Args:
            coil_name (str): Nombre del coil a leer (ej: "Y010").
        Returns:
            bool: Valor booleano leido.
        """
        try:
            coil = coil_name.lower()
            key = ''.join(re.findall(r'[A-Za-z]', coil))
            address = self.coils[key]["address"]
        except KeyError as e:
            raise ModbusBorunteError(f"Coil no encontrado: {e}")
        return self.read_coils(address=address, count=1)
    
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
            response = self.read_coils(address=start_address, count=count)
            if response.isError():
                raise ModbusBorunteError(f"Error al leer coils desde {start_address} (count={count})")
            values = response.bits[:count]
            sub_result = dict(zip(mem_addr, values))
            result[name] = sub_result
        
        return result
    
    def read_status(self, register_name):
        """
        Lee un registro Modbus y lo interpreta como int16 o float32.
        Args:
            register_name (str): Nombre del registro a leer (ej: "global_velocity").
        Returns:
            list of float or int, o None si hay error.
        """
        try:
            address = self.registers["machine_status"][register_name]["address"]
            length = self.registers["machine_status"][register_name]["length"]
            double_bit = self.registers["machine_status"][register_name]["double_bit"]
        except KeyError as e:
            raise ModbusBorunteError(f"Registro no encontrado: {e}")
        return self.read_modbus_values(address, length, double_bit)

    def read_all_status(self):
        """
        Lee todos los registros Modbus y los interpreta como int16 o float32.
        Returns:
            dict: Diccionario con los nombres de los registros como claves y los valores como valores.
        """
        result = {}
        for name in self.registers["machine_status"].keys():
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
            raise ModbusBorunteError("⚠️ Direccion fuera de rango (tiene que estar entre 800 y 890) o la cantidad de addresses es menor a 1")
        
        start_address = base_modbus + (address_number - 800) * 2
        values = self.read_modbus_scaled_ints(start_address, number_of_addresses)
        # creacion de diccionario
        logical_keys = [str(800 + i) for i in range(number_of_addresses)]
        return dict(zip(logical_keys, values))
    
    def read_all_memory_address(self):
        """
        Lee todos los registros Modbus (800 - 890) y los interpreta como int32.
        Returns:
            dict: Diccionario con los nombres de los registros como claves y los valores como valores.
        """
        # 2 batches
        batch1 = self.read_memory_address(800, 40)
        batch2 = self.read_memory_address(840, 50)
        return {**batch1, **batch2}
    
    def read_all_borunte_data(self):
        """
        Lee todos los registros Modbus, colis y addresses.
        Returns:
            dict: Diccionario con los nombres de los registros como claves y los valores como valores.
        """
        return {
            "addresses": self.read_all_memory_address(),
            "coils": self.read_all_outputs(),
            "status": self.read_all_status()
        }
    
    def write_output(self, coil_name: str, value: bool):
        """
        Escribe un valor booleano a la direccion correspondiente.
        Args:
            coil_name (str): Nombre del coil a escribir (ej: "Y010").
            value (bool): Valor booleano a escribir.
        Returns:
            dict: Diccionario con el status, function_code, address y value
        """ 
        try: 
            coil = coil_name.lower()
            key = ''.join(re.findall(r'[A-Za-z]', coil))
            address = self.coils[key]["addresses"][coil]
        except KeyError as e:
            raise ModbusBorunteError(f"Coil no encontrado: {e}")
        
        response = self.write_coil(address=address, value=value)

        return {"status": not response.isError(), "function_code": response.function_code, "address": address, "value": value} 
    
    def write_memory_address(self, address_number: int, value: list[int]):
        """
        Escribe múltiples valores int32 desde Modbus y los escala (útil para milésimas).
        
        Args:
            address_number (int): direccion inicial Modbus (800 - 890)
            value (list): lista de enteros a escribir

        Returns:
            dict: Diccionario con el status, function_code, address y value
        """
        if address_number < 800 or address_number > 890 or address_number + len(value) - 1 > 890 or len(value) < 1:
            raise ModbusBorunteError("⚠️ Direccion fuera de rango (tiene que estar entre 800 y 890) o la cantidad de valores es menor a 1")
        
        base_modbus = self.registers["address"]["800"]
        registros_modbus = []
        for val in value:
            high, low = struct.unpack('>HH', struct.pack('>i', val))
            registros_modbus.extend([high, low])

        start_address = base_modbus + (address_number - 800) * 2

        response = self.write_registers(address=start_address, values=registros_modbus)
    
        return {"status": not response.isError(), "function_code": response.function_code, "address": start_address, "values": value}

    def send_command(self, register_name, value):
        """
        Envia un comando con el nombre correspondiente activandolo con un 1
        Args:
            register_name (str): Nombre del registro a escribir (ej: "start_button").
            value (int): Valor entero a escribir. (ej: 1)
        Returns:
            dict: Diccionario con el status, function_code, address y value
        """
        try:
            address = self.registers["command"][register_name]["address"]
        except KeyError as e:
            raise ModbusBorunteError(f"Comando no encontrado: {e}")
        
        response = self.write_register(address=address, value=value)
        
        return {"status": not response.isError(), "function_code": response.function_code, "address": address, "value": value}
    
    def start_button(self):
        return self.send_command("start_button", 1)
    
    def pause_button(self):
        return self.send_command("pause_button", 1)
    
    def single_loop_button(self):
        return self.send_command("single_loop", 1)
    
    def stop_button(self):
        return self.send_command("stop_button", 1)
    
    def force_stop_button(self):
        return self.send_command("force_stop", 1)
    
    def clear_alarm_button(self):
        return self.send_command("clear_alarm", 1)
    
    def clear_alarm_and_resume_button(self):
        return self.send_command("clear_alarm_and_resume", 1)
    
    def modify_global_velocity(self, value: int):
        """
        Modifica la velocidad global.
        Args:
            value (int): Valor entero a escribir (0.0-100.0) maximo 1 decimal.
        Returns:
            dict: Diccionario con el status, function_code, address y value
        """
        if not (0 <= value <= 100.0):
            raise ModbusBorunteError("⚠️ Valor fuera de rango (0-100.0)")
        
        value = int(value * 10)
        address = self.registers["machine_status"]["global_velocity"]["address"]
        response = self.write_register(address=address, value=value)

        return {"status": not response.isError(), "function_code": response.function_code, "address": address, "value": value}

    def proceso_01(self, data: dict):
        """
        Proceso 1: paletizado frontal con ajuste XY, cantidad, altura de stack y velocidad.
        Args:
            data (dict): {
                "pick": [x, y, z, rx, ry, rz],
                "put": [x, y, z, rx, ry, rz],
                "cantidad": int,
                "x": float,
                "y": float,
                "altura": float,
                "velocidad": int
            }
        Returns:
            dict: Resultados de verificación
        """
        required_keys = ["pick", "put", "cantidad", "x", "y", "altura", "velocidad"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Falta el parámetro requerido: {key}")
            
        if not isinstance(data["pick"], list) or len(data["pick"]) != 6:
            raise ValueError("`pick` debe ser una lista de 6 floats.")
        
        if not isinstance(data["put"], list) or len(data["put"]) != 6:
            raise ValueError("`put` debe ser una lista de 6 floats.")
        
        for float_key in ["x", "y", "altura"]:
            if not isinstance(data[float_key], (float, int)):
                raise ValueError(f"{float_key} debe ser un número.")

        for int_key in ["cantidad", "velocidad"]:
            if not isinstance(data[int_key], int):
                raise ValueError(f"{int_key} debe ser un entero.")

        pick_scaled = [int(i * 1000) for i in data["pick"]]
        put_scaled = [int(i * 1000) for i in data["put"]]

        self.write_memory_address(800, pick_scaled)
        self.write_memory_address(810, put_scaled)

        compe = (data["cantidad"] - 1) * data["altura"]
        self.write_memory_address(820, [
            int(data["x"]*1000), int(data["y"]*1000),
            int(compe*1000), data["altura"]*1000,
            data["cantidad"], data["velocidad"]
        ])

        self.modify_global_velocity(data["velocidad"])

        # Posible start
        # self.start_button()
        
        return {"status": True}
    