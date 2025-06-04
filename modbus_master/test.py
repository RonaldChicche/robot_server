from ModbusTCPClient import ModbusDictionaryClient

if __name__ == "__main__":
    modbus = ModbusDictionaryClient(
        ip="127.0.0.1",
        port=502,
        json_path="diccionario_registros.json"
    )

    if modbus.connect():
        valor = modbus.read("version_text_start")
        print("Valor leído:", valor)
        print("Registro:", modbus.registers["version_text_start"])
        modbus.close()
    else:
        print("❌ No se pudo conectar")
