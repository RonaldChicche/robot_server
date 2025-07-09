import time
import json
import os
from common.utils import load_keys, create_redis_client, create_kafka_producer
#from process_logic import handle_process


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")


def handle_process(redis_client, keys, process_id, params):
    # Ejemplo de lógica simple
    peso = params.get("peso", 0)
    cantidad = params.get("cantidad", 1)

    # Decisión de robot
    robot_id = "01" if peso < 10 else "02"

    # Cálculos ficticios de valores
    dx = 100
    dy = 200
    height = 1200
    velocity = 300
    pickup = [100, 200, 300, 0, 0, 0]
    place = [500, 400, 300, 0, 0, 0]

    # Escribir en Redis
    redis_client.set(keys["process_coordinator"]["robot_dx_template"].format(id=robot_id), dx)
    redis_client.set(keys["process_coordinator"]["robot_dy_template"].format(id=robot_id), dy)
    redis_client.set(keys["process_coordinator"]["robot_height_template"].format(id=robot_id), height)
    redis_client.set(keys["process_coordinator"]["robot_velocity_template"].format(id=robot_id), velocity)
    redis_client.set(keys["process_coordinator"]["robot_pickup_template"].format(id=robot_id), json.dumps(pickup))
    redis_client.set(keys["process_coordinator"]["robot_place_template"].format(id=robot_id), json.dumps(place))
    redis_client.set(keys["process_coordinator"]["robot_amount_template"].format(id=robot_id), cantidad)

    # Comando para ejecutar
    cmd = {
        "cmd": "start_pick_and_place",
        "params": {},
        "process_id": process_id
    }
    redis_client.set(keys["process_coordinator"]["robot_cmd_template"].format(id=robot_id), json.dumps(cmd))
    print(f"🧾 Comando generado para robot:{robot_id}")



def main():
    keys = load_keys()
    redis_client = create_redis_client(REDIS_HOST, REDIS_PORT)
    kafka_producer = create_kafka_producer(KAFKA_BROKER)
    print("🧠 Process coordinator started")

    while True:
        # Verifica si hay definido un proceso en el buffer si no ignora todo
        #if !proceso: continue

        # Maquina de estado:
        # LECTURA:  lee parametros de OPC -> 
        # params = {
        #     "ancho_caja": self.outer.values["ancho_caja"],
        #     "long_barra": self.outer.values["long_barra"],
        #     "ancho_barra": self.outer.values["ancho_barra"],
        #     "espesor": self.outer.values["espesor"],
        #     "peso": self.outer.values["peso"],
        #     "cantidad": self.outer.values["cantidad"],
        #     "no_carro": self.outer.values["no_carro"]
        # } 
        # 
        #        
        pass


        #time.sleep(0.5)


if __name__ == "__main__":
    main()