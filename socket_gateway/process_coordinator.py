import time
import json
import logging
import signal, sys
import os
from common.utils import load_keys, create_redis_client, create_kafka_producer
#from process_logic import handle_process

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")

logger = logging.getLogger("ProcessCoordinator")

redis_client = None
kafka_producer = None

def handle_process(redis_client, keys, process_trama, compe_1={}, compe_2={}):
    """ 
    process: {
        "order_id": 1,
        "type": "process",
        "name": "send_data",
        "params": {
            "long_caja": 1100    #### interno de la caja
            "ancho_caja": 150.0,
            "altura_caja" : 350,  # new
            "long_barra": 1000.0,
            "ancho_barra": 50.0,
            "espesor": 10.0,
            "peso": 10.0,
            "cantidad_x": 1,
            "cantidad_z": 1,
            "no_carro": 1,
            "w1" : 0.5, # new
            "w2" : 0.5  # new
        }
    }
    trama a generar: 
        data (dict): {
                "pick": [x, y, z, rx, ry, rz],
                "put": [x, y, z, rx, ry, rz],
                "cantidad_x": int,
                "cantidad_z": int,
                "dx": float,
                "dy": float,
                "espesor": float,
                "ancho" : float,
                "velocidad": int,
                "bit_coordinador": int,
                "compensacion_x": float
            }
    """
    # tope piston = >>>>>> y tope -> 372.671
    parametros = process_trama["params"]
    largo_gripper = 2069
    ancho_gripper = 121
    bit_compensacion = False
    bit_delgados = False
    compenza_desfase = 0
    compenza_desfase_y = 0

    # esquina de barra solo para este caso
    tope_x0 = 1650.350 + 18 - 11 + 3 -7 - 10
    tope_y0 = -1864.266
    tope_z0 = 352.951 - 2

    # calibracion pick
    x_0 = tope_x0 + ancho_gripper/2
    y_0 = tope_y0 - largo_gripper/2
    z_0 = tope_z0 + 100 # prueba y error
    u_0 = -178.133
    v_0 = -1.084
    w_0 = -151.072

    # calculo de pick
    ## Calculo inicial de Pick 
    ## X : X_0 - ancho de barra/2
    ## Y : Y_0 + largo de barra/2
    ## Z : Z_0 + espesor
    ## U, V, W : U_0, V_0, W_0

    if float(parametros["ancho_barra"]) > 70:
        pick_x = x_0 - float(parametros["ancho_barra"]) / 2
    else:
        pick_x = x_0 - float(parametros["ancho_barra"])
        bit_delgados = True

    if pick_x > tope_x0 and float(parametros["ancho_barra"]) > 70:
        pick_x = tope_x0
        compenza_desfase = ancho_gripper - float(parametros["ancho_barra"])
        bit_compensacion = True

    pick_y = y_0 + float(parametros["long_barra"]) / 2
    if bit_compensacion: # or bit_delgados
        compenza_desfase_y = -1240 - pick_y
        pick_y = -1240
    
    pick_z = z_0 + float(parametros["espesor"])
    pick_u = u_0
    pick_v = v_0
    pick_w = w_0

    # esquina de caja
    tope_x1_1 = 1976.422 + 4.5 + 4 + 10.1 - 17 + 2
    # 2817.6
    tope_x1_2 = 2651.369 + 139.1 + 7 - 62.56 - 7 + 16 + 9 -21
    # tope_y1 = y_0 
    tope_y1 = -372.671 + largo_gripper/2  #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Nuevo calculo
    tope_z1_1 = 127   ## nivel de la mesa
    tope_z1_2 = 127
    ## X_1_1 : (Ubicacion de Tope de guia en mesa 1 con gripper - Largo de gripper/2)
    ## X_1_2 : (Ubicacion de Tope de guia en mesa 2 con gripper - Largo de gripper/2)
    ## Y_1 : tope de y_0 ya que esta alineado pero 
    ## Z_1 : al nivel de una caja mas un juego (se tiene que estandarizar las medidas de estas en cuanto a altura)
    ## U_1, V_1, W_1 : U_0, V_0, W_0

    x_1_1 = tope_x1_1 - ancho_gripper/2 + 2
    x_1_2 = tope_x1_2 - ancho_gripper/2
    # y_1 = y_0
    y_1 = tope_y1  #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Nuevo calculo

    # calculo de put 
    ## X : (if no_carro == 1,2) X_1_1, X_1_2 + ancho de caja/2 - (ancho de barra/2 x (cantidad_x - 1))
    ## Y : Y_1 + largo de caja/2 (ajuste por medio de largo de caja)
    ## Y : Y_1 - largo de caja/2  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Nuevo calculo
    ## Z : Z_1 + espesor
    ## U, V, W : U_0, V_0, W_0

    # ajuste de carro ------ VALORES ACTUALES FUNCIONALES
    if int(parametros["no_carro"]) == 1:
        # relativos 
        dz_pick = 200
        dz_p = 250 - 150
        dz_n = -dz_p
        x_1 = x_1_1 
        z_1 = tope_z1_1 + float(parametros.get("altura_caja")) + 250 # prueba y error
        # u_1 = -178.133
        # v_1 = -1.084
        # w_1 = -151.072
        #w_1 = -149.939
        # w_compe = parametros.get("w1", 0)
        # if abs(w_1 - w_compe) > 0.1 and w_compe != 0:
        #     logger.info(f"🟢 Compensacion de giro || {w_compe}")
        #     w_1 = w_compe

    elif parametros["no_carro"] == 2:
        # relativos 
        dz_pick = 600
        dz_p = 550 + 100 - 150
        dz_n = -dz_p + 100
        x_1 = x_1_2 
        z_1 = tope_z1_2 + float(parametros.get("altura_caja")) + 550 # prueba y error
        
        # w_compe = parametros.get("w2", 0)
        # if abs(w_1 - w_compe) > 0.1 and w_compe != 0:
        #     logger.info(f"🟢 Compensacion de giro || {w_compe}")
        #     w_1 = w_compe

    u_1 = -178.133
    v_1 = -1.084
    w_1 = -151.072

    if bit_delgados:
        put_x = x_1 + float(parametros["ancho_caja"])/2 - (float(parametros["ancho_barra"]) * ((int(parametros["cantidad_x"]) + 1)//2 - 1))
    else:
        put_x = x_1 + float(parametros["ancho_caja"])/2 - (float(parametros["ancho_barra"])/2 * (float(parametros["cantidad_x"]) - 1)) - compenza_desfase/2
    
    # put_y = y_1 + float(parametros["long_caja"])/2
    # if bit_compensacion: # or bit_delgados: 
    #     put_y = put_y + compenza_desfase_y
    # put_y = put_y - 190 # desfase por linea
    put_y = y_1 - float(parametros["long_caja"])/2       #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Nuevo calculo
    if bit_compensacion:  
        put_y = put_y + compenza_desfase_y  #### (SE mantiene el signo)
    # ASUMIMOS SIN DESFASE
    put_z = z_1 + float(parametros["espesor"])
    put_u = u_1
    put_v = v_1
    put_w = w_1


    ancho = 0
    if bit_delgados:
        bit_compensacion = 2
        ancho = float(parametros["ancho_barra"]) * 2
        compenza_desfase = float(parametros["ancho_barra"])
        ct_x = (int(parametros["cantidad_x"]) + 1)//2
    else:
        ancho = float(parametros["ancho_barra"])
        ct_x = int(parametros["cantidad_x"])

    if ct_x == 3 and int(parametros["no_carro"]) == 2:
        pick_y = pick_y + 300
        put_y = put_y + 300
    
    # generacion de trama data(dict)
    data = {
        "pick": [pick_x, pick_y, pick_z, pick_u, pick_v, pick_w],
        "put": [put_x, put_y, put_z, put_u, put_v, put_w],
        "cantidad_z": int(parametros["cantidad_z"]),
        "cantidad_x": ct_x,
        "dz_p": dz_p,
        "dz_n": dz_n,
        "dz_pick": dz_pick,
        "espesor": float(parametros["espesor"]),
        "ancho" : ancho,
        "bit_coordinador": False,
        "bit_compensacion": bit_compensacion,
        "compenzacion_desfase": compenza_desfase
        #"compensacion_x": float(parametros["cantidad_x"]) * float(parametros["ancho_barra"])
    }

    # trama method para proceso_01
    trama = {
        "order_id": process_trama["order_id"],
        "robot_id" : "01",
        "type": "method",
        "name": "proceso_01",
        "params": data
    }

    # get redis key
    # redis_key = keys["process_coordinator"]["robot_cmd_template"].format(id="01")
    # redis_client.set(redis_key, json.dumps(trama))
    
    return trama


def graceful_shutdown():
    logger.info("🛑 Señal de apagado recibida. Cerrando conexiones...")
    try: 
        if redis_client:
            redis_client.close()
            logger.info("✅ Redis cerrado")
    except Exception as e:
        logger.error(f"⚠️ Error cerrando conexiones: {e}", exc_info=True)
    sys.exit(0)


def main():
    global redis_client, kafka_producer
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)


    keys = load_keys(path="common/redis_keys.yaml")
    try:
        redis_client = create_redis_client(REDIS_HOST, REDIS_PORT)
        #kafka_producer = create_kafka_producer(KAFKA_BROKER)
    except:
        logger.error(f"❌ Error inesperado al iniciar: {e}", exc_info=True)
        graceful_shutdown()
    
    logger.info("🟢 Proceso coordinador iniciado")

    while True:
        try: 
            # Verifica si hay definido un proceso en el buffer si no ignora todo
            process_raw = redis_client.get(keys["process_coordinator"]["process_template"])
            if process_raw is not None:
                process = json.loads(process_raw)
                logger.info(f"🟢 Proceso recibido: {process}")
                trama = handle_process(redis_client, keys, process)
                logger.info(f"🟢 Trama generada: {trama}")
                redis_client.delete(keys["process_coordinator"]["process_template"])

                # save on process_back_template
                redis_key = keys["process_coordinator"]["process_current"]
                redis_client.set(redis_key, json.dumps(process))

                # Envia trama a robot 01
                redis_key = keys["process_coordinator"]["robot_cmd_template"].format(id="01")
                redis_client.lpush(redis_key, json.dumps(trama))
                redis_client.expire(redis_key, 5)
                logger.info(f"🟢 Trama enviada a robot 01: {trama}")

                # # Envia trama a robot 02
                # redis_key = keys["process_coordinator"]["robot_cmd_template"].format(id="02")
                # redis_client.lpush(redis_key, json.dumps(trama))
                # logger.info(f"🟢 Trama enviada a robot 02: {trama}")

            # Verifica estado del proceso en ejecucion

        except Exception as e:
            logger.error(f"❌ Error inesperado al procesar: {e}", exc_info=True)
            redis_client.delete(keys["process_coordinator"]["process_template"])
            #graceful_shutdown()
            time.sleep(1)
        time.sleep(0.5)


if __name__ == "__main__":
    main()




# Proceso de pick and place x z 
# ....DDDDDDD.....1
# ....DDDDDDD.....2
# ....DDDDDDD.....3

## Entradas PLC:
##     - long_caja # medida interna
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
## Y : es el tope Y_0 + longitud de caja / 2
## Z : Z_1 + espesor
## U, V, W : U_0, V_0, W_0

## Entradas:
##     - pick: [x, y, z, rx, ry, rz]  || 800, 801, 802, 803, 804, 805 (fijo)
##     - put: [x, y, z, rx, ry, rz]   || 810, 811, 812, 813, 814, 815 ()
##     - cantidad_z: int              || 820
##     - cantidad_x: int              || 821
##     - dx: float                    || 822
##     - dy: float                    || 823
##     - espesor: float               || 824
##     - ancho: float                 || 825
##     - velocidad: int               || 826
##     - bit_coordinator: int         || 827
##     - compensacion_x: float        || 828

##     No es parametro es algo que la misma funcion hara como parte de su logica
##     - selector                     || 850
##     - compensacion(barras delgadas)|| 851
##     - cantidad a compenzar         || 852


## Salidas:
##     - y20 : Actuador neumatico
##     ------ Bits de estado
##     - y30 : (INICIO) Posicion para paletizar
##     - y31 : Posicion de deposicion de barra
##     - y32 : (PALETIZADO) Confirmaacion de paletizado (despues de soltar la barra)
##     - y33 : (FIN) Posicion de reposo (Proceso terminado)
##     - y35 :
##     - y36 :
##     - y37 : Confirmacion de home (se prende solo cuando ejecuta home en cualquier otra accion se apaga)
##     ------ Estos vienen de fuera de la logica del progrma interno del robot
##     - y40 : Bit de confirmacion de barra lista para VOLTEAR (viene de OPC)
##     - y41 : Bit de confirmacion de coordinacion (viene de Coordinador - DESHABILITADO)
##     - y42 : Bit de confirmacion de barra lista para depositar (viene de OPC)
##     - y45 : Bit de confirmacion de lectura de datos para proceso (DE donde sea)


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



## manejo de estados

## entrada ======
## start button
## stop button
## pause button

## green -> y10
## yello -> y11
## red -> y12

## salida =======
## bit green opc (G0)
## bit yello opc (Y0)
## bit red opc   (R0)

## -> estados 
# Vacio -> (G0, Y0, R0)
# Running -> (G1, Y0, R0)
# Paused -> (G0, Y1, R0)
# Stopped -> (G0, Y0, R1)
# Terminado -> (G0, Y0, R0)

## caso 1 - inicio fin normal
## manda start Button
## y10 ON -> proceso Running 
## bits proceso terminado y33 ON
## proceso Terminado = y10 and y33 (ambos ON)

## caso 2 -> pausa
## manda start Button
## y10 ON -> proceso Running
## manda pause Button 
## y11 ON -> proceso Paused
## manda start Button
## y10 ON -> proceso Running
## bits proceso terminado y33 ON
## proceso Terminado = y10 and y33 (ambos ON)

## caso 3 -> parada
## manda start Button ( - Empieza proceso)
## y10 ON -> proceso Running
## manda stop Button
## y12 ON -> proceso Stopped ( - Termina proceso)
## orden y30, y32, y33 OFF (- Reinicio de proceso)
## orden clear counters (- Reinicio de proceso)
## espera 2 segundos -> proceso Vacio
## manda start Button
## y10 ON -> proceso Running 
## bits proceso terminado y33 ON
## proceso Terminado = y10 and y33 (ambos ON)