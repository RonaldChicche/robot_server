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




# Proceso de pick and place x z 
# ....DDDDDDD.....1
# ....DDDDDDD.....2
# ....DDDDDDD.....3


## Entradas PLC:
##     - ancho_caja  
##     - long_barra
##     - ancho_barra
##     - espesor
##     - peso
##     - cantidad_x
##     - cantidad_z
##     - no_carro

## calibracion pick (X_0 y Y_0 representan la esquina de los topes -| )
##      tope X_0         _________________
##                                       |
##                       Tope Y_0        |
##  
## X_0 : Alinear con medio de barra y tope de barra fijo + ancho de gripper/2 (primero esto)
## Y_0 : ALinear con tope de barra fijo - largo de gripper/2
## Z_0 : poner en distancia de succion y restar el espesor de la barra + altura relativa designada (200)
## U_0, V_0, W_0 : Juego con respecto de la barra


##  largo de barrra
## ________________________________
#$ |                               |
#$ |                               |    ancho de barra
#$ |_______________________________| 

## Lo mismo para el gripper +++++++++++++++

## Calculo inicial de Pick 
## X : X_0 - ancho de barra/2
## Y : Y_0 + largo de barra/2
## Z : Z_0 + espesor
## U, V, W : U_0, V_0, W_0


## calibracion de Put
##                                 |
##                    Tope Y_1     |
##      tope X_1      _____________|

## X_1_1 : (Ubicacion de Tope de guia en mesa 1 con gripper - Largo de gripper/2)
## X_1_2 : (Ubicacion de Tope de guia en mesa 2 con gripper - Largo de gripper/2)
## Y_1 : irrelevante (la trayectoria va a ser recta)
## Z_1 : al nivel de una caja mas un juego (se tiene que estandarizar las medidas de estas en cuanto a altura)
## U_1, V_1, W_1 : U_0, V_0, W_0


## Calculo inicial de Put 
## X : (if no_carro == 1,2) X_1_1, X_1_2 + ancho de caja/2 - (ancho de barra/2 x (cantidad_x - 1))
## Y : irrelevante (la trayectoria va a ser recta)
## Z : Z_1 + espesor
## U, V, W : U_0, V_0, W_0

## Entradas:
##     - pick: [x, y, z, rx, ry, rz]  || 800, 801, 802, 803, 804, 805 (fijo)
##     - put: [x, y, z, rx, ry, rz]   || 810, 811, 812, 813, 814, 815 (no sirve)
##     - cantidad_z: int              || 820
##     - cantidad_x: int              || 821
##     - dx: float                    || 822
##     - dy: float                    || 823
##     - espesor: float               || 824
##     - ancho: float                 || 825
##     - velocidad: int               || 826
##     - bit_coordinator: int         || 827
##     - compensacion_x: float        || 828
##     - selector                     || 829



## Salidas:
##     - y20 : Actuador neumatico
##     - y30 : Posicion para paletizar
##     - y31 : coodinador de robots (espera que ambos enciendan y30)
##     - y32 : Bit de confirmacion de barra lista
##     - y33 : Posicion de deposicion de barra
##     - y33 : Capa terminada (barras en un mismo nivel de paletizado)


## Programa Borunte:  Parte de un reposo al que vuelve al final
## set target_counter_x = cantidad_x  (821)
## set target_counter_z = cantidad_z  (820)
## clear current_counter_x = 0
## clear current_counter_z = 0
## Go posicion inicial   (guarda aspecto en una posicion fija y asegura con los joints) 
## Go posicion inicial por joints
## Bucle ------------------------------------------------------
## Go posicion de paletizado (y calculado por coodinador // fijo) (800 - 805)
## Enciende y30
## If bit_coordinator == 1 -> Espera hasta que y31 se active (coordinador de robots)
## Espera hasta que y32 se active  (barra lista)
## Go Movimiento relativo -200 z 
## Activa y20 : neumatico de paletizado
## Espera 2 segundos
## Go Movimiento relativo +200 z
## Go posicion de deposicion (y calculado por coodinador // variable por compensar en x y z)
#   (810 - 815)
## Go Movimiento relativo -200 z
## Espera 2 segundos
## Desactiva y20 : neumatico de paletizado
## Go Movimiento relativo +200 z
## Enciende y33
## put x = put x + ancho de barra    (810 + 825)
## Set counter_x + 1
## if current_counter_x < target_counter_x -> Bucle
## Clear current_counter_x = 0
## put x = put x - compensacion_x   (810 - 828)
## put z = put z + espesor          (812 + 824)
## Set counter_z + 1
## if current_counter_z < target_counter_z -> Bucle
## Clear current_counter_z = 0
## Go posicion de reposo
