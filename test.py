
def handle_process(process_trama):
    """ 
    process: {
        "order_id": 1,
        "type": "process",
        "name": "send_data",
        "params": {
            "ancho_caja": 150.0,
            "largo_caja": 1100,
            "long_barra": 1000.0,
            "ancho_barra": 50.0,
            "espesor": 10.0,
            "peso": 10.0,
            "cantidad_x": 1,
            "cantidad_z": 1,
            "no_carro": 1
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
    parametros = process_trama["params"]
    # largo_gripper = 205.5
    # ancho_gripper = 12.1

    largo_gripper = 200
    ancho_gripper = 10

    # esquina de barra solo para este caso
    tope_x0 = 0
    tope_y0 = 0
    tope_z0 = 300  # a nivel con barra

    # calibracion pick
    x_0 = tope_x0 + ancho_gripper/2
    y_0 = tope_y0 - largo_gripper/2
    z_0 = tope_z0 - float(parametros["espesor"]) + 200 # prueba y error
    u_0 = 0
    v_0 = 0
    w_0 = 0
    print(f"pick 0 obtenido: {x_0} | {y_0} | {z_0}")

    # calculo de pick
    ## Calculo inicial de Pick 
    ## X : X_0 - ancho de barra/2
    ## Y : Y_0 + largo de barra/2
    ## Z : Z_0 + espesor
    ## U, V, W : U_0, V_0, W_0

    pick_x = x_0 - float(parametros["ancho_barra"]) / 2
    pick_y = y_0 + float(parametros["long_barra"]) / 2
    pick_z = z_0 + float(parametros["espesor"])
    pick_u = u_0
    pick_v = v_0
    pick_w = w_0

    # esquina de caja
    tope_x1_1 = 300
    tope_x1_2 = 500
    tope_y1 = tope_y0   # alineado con el otro tope
    tope_z1 = 100   # a nivel sin barra

    ## X_1_1 : (Ubicacion de Tope de guia en mesa 1 con gripper - Largo de gripper/2)
    ## X_1_2 : (Ubicacion de Tope de guia en mesa 2 con gripper - Largo de gripper/2)
    ## Y_1 : irrelevante (la trayectoria va a ser recta)
    ## Z_1 : al nivel de una caja mas un juego (se tiene que estandarizar las medidas de estas en cuanto a altura)
    ## U_1, V_1, W_1 : U_0, V_0, W_0

    x_1_1 = tope_x1_1 - ancho_gripper/2
    x_1_2 = tope_x1_2 - ancho_gripper/2
    y_1 = y_0
    z_1 = tope_z1 + 200 # prueba y error
    u_1 = u_0
    v_1 = v_0
    w_1 = w_0

    print(f"put 0 obtenido: {x_1_1} | {x_1_2} | {y_1} | {z_1}")

    # calculo de put 
    ## X : (if no_carro == 1,2) X_1_1, X_1_2 + ancho de caja/2 - (ancho de barra/2 x (cantidad_x - 1))
    ## Y : irrelevante (la trayectoria va a ser recta)
    ## Z : Z_1 + espesor
    ## U, V, W : U_0, V_0, W_0

    if int(parametros["no_carro"]) == 1:
        put_x = x_1_1 + float(parametros["ancho_caja"])/2
    elif parametros["no_carro"] == 2:
        put_x = x_1_2 + float(parametros["ancho_caja"])/2
    put_y = y_1 + float(parametros["long_caja"])/2
    put_z = z_1 + float(parametros["espesor"])
    put_u = u_1
    put_v = v_1
    put_w = w_1


    # generacion de trama data(dict)
    data = {
        "pick": [pick_x, pick_y, pick_z, pick_u, pick_v, pick_w],
        "put": [put_x, put_y, put_z, put_u, put_v, put_w],
        "cantidad_z": parametros["cantidad_z"],
        "cantidad_x": parametros["cantidad_x"],
        "dx": 0,
        "dy": 0,
        "espesor": parametros["espesor"],
        "ancho" : parametros["ancho_barra"],
        "velocidad": 200,
        "bit_coordinador": False,
        "compensacion_x": float(parametros["cantidad_x"]) * float(parametros["ancho_barra"])
    }

    # trama method para proceso_01
    trama = {
        "order_id": process_trama["order_id"],
        "robot_id" : "01",
        "type": "method",
        "name": "proceso_01",
        "params": data
    }

    return trama



process = {
    "order_id": 1,
    "type": "process",
    "name": "send_data",
    "params": {
        "ancho_caja": 150.0,
        "long_caja": 3100.0,
        "long_barra": 3000.0,
        "ancho_barra": 50.0,
        "espesor": 10.0,
        "peso": 21.0,
        "cantidad_x": 1,
        "cantidad_z": 1,
        "no_carro": 1
    }
}


trama = handle_process(process)

print(f"Trama obtenida: {trama}")


