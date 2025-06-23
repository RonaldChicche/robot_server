from ModbusBorunteClient import ModbusBorunteClient

import keyboard

# orden estándar: 
#  <timestamp> <level> [<component>] <message>

# home x 1500 y -125 z 1000 u 180 v 0 w -151
# punto de arriba x 2476.343 y -125.616 z 822.786 u 180 v 0 w -151 
# Ejemplo : orden estándar: 
# <timestamp> <level> [<component>] <message>

def proceso_1(client: ModbusBorunteClient, data: dict):
    """
    Proceso 1: paletizado frontal ajuste en XY, cantidad, altura de stack (Z) y velocidad
    Args:
        client: ModbusBorunteClient
        data: dict -> {cantidad: int, x: float, y: float, velocidad: int, altura: int}
    Returns:
        bool: True si se pudo realizar el proceso
    """    
    # Punto de inicio pick en memoria
    pick = [1654.937, -125.636, 1100, 180, 0, -151]
    pick = [int(i*1000) for i in pick]
    client.write_memory_address(800, pick)
    # Punto de inicio put en memoria
    put = [2476.343, -125.616, 822.786, 180, 0, -151]
    put = [int(i*1000) for i in put]
    client.write_memory_address(810, put)
    # compensaciones x 820 y 821 z 822 compeZ_init 823 altura 824 cant 825 vel
    compe = (data["cantidad"] - 1) * data["altura"]
    client.write_memory_address(820, [int(data["x"]*1000), int(data["y"]*1000), int(compe*1000), data["altura"]*1000, data["cantidad"], data["velocidad"]])
    # establece la velocidad 
    client.modify_global_velocity(data["velocidad"])
    # start el proceso 1 ----------------
    #client.start_button()
    print("Proceso 1 iniciado -------------------- *********")
    # lee los registros para verificar
    result = {
        "pick": client.read_memory_address(800, 6),
        "put": client.read_memory_address(810, 6),
        "compensations": client.read_memory_address(820, 6),
        "status": client.read_all_status()
    }

    # read alarms por poner

    return result

def main():
    client = ModbusBorunteClient(host='127.0.0.1')

    if client.connect():
        print("✅ Conectado")

        data = {
            "cantidad": 3,
            "x": 0.0,
            "y": 154.9,
            "velocidad": 90,
            "altura": 50
        }

        result = proceso_1(client, data)
        print(result)
    else:
        print("❌ No se pudo conectar")
        return None

    # loop wait for key instruccions
    while True:
        if keyboard.is_pressed('q'):
            result = {
                "pick": client.read_memory_address(800, 6),
                "put": client.read_memory_address(810, 6),
                "compensations": client.read_memory_address(820, 6),
                "status": client.read_all_status()
            }
            print("-------------------------------------------------------")
            print("Result: ", result)
        if keyboard.is_pressed('w'):
            print("Info -------------------------------------------------------------------------- ///////////")
            info = client.read_all_borunte_data()
            print("Info:", info)
        if keyboard.is_pressed('z'):
            client.stop_button()
            client.stop_button()
            resp = client.close()
            if resp: 
                print("❌ Desconectado")
            else: 
                client.force_stop_button()
                print("✅ Desconectado")
            break
        if keyboard.is_pressed('e'):
            resp = client.force_stop_button()
            if resp:
                print("✅ Forzado de emergencia")
        if keyboard.is_pressed('s'):
            client.start_button()
            print("✅ Iniciado")

if __name__ == "__main__":
    main()
