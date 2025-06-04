from ModbusTCPClient import ModbusTCPClient


def main():
    modbus = ModbusTCPClient(ip='127.0.0.1', port=502)

    if modbus.connect():
        print("✅ Conectado")

        # Leer 2 registros desde dirección 0
        values = modbus.read_holding_registers(0, 2)
        print("Leído:", values)

        # Escribir 1234 en dirección 0
        modbus.write_single_register(0, 1234)

        # Escribir múltiples registros
        modbus.write_multiple_registers(10, [111, 222, 333])

        modbus.close()
    else:
        print("❌ No se pudo conectar")


if __name__ == "__main__":
    main()