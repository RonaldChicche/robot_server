
import socket
import json
import time
from datetime import datetime

class RobotStateMachine:
    def __init__(self):
        self.state = "Vacio"
        self.awaiting_clean = False

    def handle_command(self, command_name: str):
        if command_name == "start_button":
            self.state = "Running"
        elif command_name == "pause_button":
            self.state = "Paused"
        elif command_name == "stop_button":
            self.state = "Stopped"
            self.awaiting_clean = True
            self.clean_time = time.time() + 4  # esperar 2 segundos sin bloquear
        return self.state
    
    def check_clean(self):
        if self.awaiting_clean and time.time() >= self.clean_time:
            self.state = "Vacio"
            self.awaiting_clean = False
            return True
        return False

    def evaluate_termination(self, outputs: dict):
        if outputs.get("y10") and outputs.get("y33"):
            self.state = "Terminado"
        return self.state
    
    def clean_state(self):
        self.state = "Vacio"

class JSONBorunteClient:
    def __init__(self, host='127.0.0.1', robot_id="01", port=9760, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.robot_id = robot_id
        self.sock = None
        self.proceso_num = 1
        self.vel_prod = 200
        self.vel_test = 100

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), self.timeout)

    def disconect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send_json(self, data):
        # requiere conexion -----------
        # if not self.sock:
        #     self.connect()
        # message = json.dumps(data)
        # self.sock.sendall(message.encode('utf-8'))
        # response = self.sock.recv(4096)
        # no requiere conexion --------
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            message = json.dumps(data)
            s.connect((self.host, int(self.port)))
            s.sendall(message.encode())
            response = s.recv(2048)
        return json.loads(response.decode())

    def read_query(self, keys, pack_id="1"):
        request = {
            "dsID": "www.hc-system.com.RemoteMonitor",
            "reqType": "query",
            "packID": pack_id,
            "queryAddr": [keys]
        }
        #print(f"Sending request: {request}")
        return self.send_json(request)

    def send_command(self, cmd_array, pack_id="1"):
        cmd_array = [*map(str, cmd_array)]
        request = {
            "dsID": "www.hc-system.com.RemoteMonitor",
            "reqType": "command",
            "packID": pack_id,
            "cmdData": cmd_array
        }
        #print(f"Sending request: {request}")
        return self.send_json(request)

    def modify_counter(self, counter_id, current, target):
        cmd_array = ["modifyCounter", counter_id, current, target] 
        return self.send_command(cmd_array, "1")
    
    def modify_stack(self, stack_id, X, Y, Z, x_count, y_count, z_count):
        cmd_array = ["modifyStack", stack_id, X, Y, Z, x_count, y_count, z_count]
        return self.send_command(cmd_array, "1")
    
    def modify_global_velocity(self, velocity):
        cmd_array = ["modifyGSPD", velocity]
        return self.send_command(cmd_array, "1")

    def write_data_single(self, addres: int, value: int, permanent: int=0):
        cmd_array = ["rewriteData", addres, value, permanent]
        return self.send_command(cmd_array, "1")
    
    def write_data_block(self, start_address: int, data: list[int], permanent: int=0):
        cmd_array = ["rewriteDataList", start_address, len(data), permanent, *data]
        return self.send_command(cmd_array, "1")

    def modify_output_y(self, output_id: int, value: bool=True):
        output_id = int(output_id)
        if 10 <= output_id <= 17:
            index = output_id - 10
        elif 20 <= output_id <= 27:
            index = output_id - 12
        elif 30 <= output_id <= 37:
            index = output_id - 14
        elif 40 <= output_id <= 47:
            index = output_id - 16
        else: return {"error": "indice invalido"}
        cmd_array = ["modifyOutput", 0, index, int(value)]
        return self.send_command(cmd_array, "1")

    def start_button(self):
        return self.send_command(["startButton"], "0")
    
    def stop_button(self):
        return self.send_command(["stopButton"])
    
    def action_stop(self):
        return self.send_command(["actionStop"])
    
    def action_pause(self):
        return self.send_command(["actionPause"])
    
    def clear_alarm(self):
        return self.send_command(["stopButton"])
    
    def clear_alarm_run_next(self):
        return self.send_command(["clearAlarmRunNext"])
    
    def clear_alarm_and_continue(self):
        return self.send_command(["clearAlarmAndContinue"])

    def proceso_01(self, pick: list, put: list, cantidad_z: int, cantidad_x: int, dx: float, dy: float, espesor: float, ancho: float, velocidad: int, bit_coordinador: int, bit_compensacion: int, compenzacion_desfase: float):
        """
        Proceso 1: paletizado frontal con ajuste XY, cantidad, altura de stack y velocidad.
        Args:
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
                "bit_compensacion": bit_compensacion,
                "compenzacion_desfase": compenza_desfase
                "compensacion_x": float
            }
        Returns:
            dict: Resultados de verificación
        """
        # Establecimiento de selector de funcion
        self.write_data_single(850, 1)
        self.proceso = 1

        compensacion_x = cantidad_x * ancho
        
        pick_scaled = [int(i * 1000) for i in pick]
        put_scaled = [int(i * 1000) for i in put]

        self.write_data_block(800, pick_scaled)
        self.write_data_block(810, put_scaled)

        self.write_data_block(820, [
            int(cantidad_z),
            int(cantidad_x),
            int(dx*1000), int(dy*1000),
            int(espesor*1000), int(ancho*1000),
            int(velocidad), 
            int(bit_coordinador),
            int(compensacion_x*1000)
        ])

        
        bit_compensacion = int(bit_compensacion)
        compenzacion_desfase = int(compenzacion_desfase*1000)
        
        self.write_data_block(851, [bit_compensacion, compenzacion_desfase])

        #self.modify_global_velocity(velocidad)
        return True

    def proceso_02(self):
        response = self.write_data_single(850, 2)
        self.proceso = 2

        time.sleep(1)
        self.start_button()

        time.sleep(1)
        self.modify_global_velocity(self.vel_test)
        self.write_data_single(850, 1)
        self.proceso = 1

        return response

    def proceso_03(self):
        ###### TEST 
        response = self.write_data_single(850, 3)
        self.proceso = 3

        time.sleep(1)
        self.start_button()

        time.sleep(1)
        self.modify_global_velocity(self.vel_test)
        self.write_data_single(850, 1)
        self.proceso = 1

        return response
    
    def proceso_04(self):
        #### rel z
        response = self.write_data_single(850, 4)
        self.proceso = 4

        time.sleep(1)
        self.start_button()

        time.sleep(1)
        self.modify_global_velocity(self.vel_test)
        self.write_data_single(850, 1)
        self.proceso = 1
        
        return response
    def proceso_05(self):
        #### HOME
        response = self.write_data_single(850, 5)
        self.proceso = 5

        time.sleep(1)
        self.start_button()
        
        time.sleep(1)
        self.modify_global_velocity(self.vel_test)
        self.write_data_single(850, 1)
        self.proceso = 1
        
        return response

    def query_all_borunte_data(self):
        """
        {
            "robot_id": "01",
            "ip": "192.168.101.22",
            "online": true,
            "status": {
                "order_id": "DIS_20250626223830_borunte_test_02",
                "addresses": {"800": 0, "801": 0, ..., "890": 0},
                "outputs": {
                    "y": {"y10": false, "y11": true, ...},
                    "m": {"m10": false, "m11": false, ... },
                    "euy": {"euy10": false,"euy11": false, ...}
                },
                "status": {
                    "movement_status": [0],
                    "home_status": [1],
                    "alarm_code": [0],
                    "global_velocity": [100],
                    "current_cycle_time": [191.729],
                    "last_cycle_time": [0.0],
                    "axis_temperature": [t1, t2, t3, t4, t5, t6],
                    "axis_position": [j1, j2, j3, j4, j5, j6],
                    "world_position": [x, y, z, u, v, w],
                    "axis_velocity": [...],
                    "axis_torque": [...],
                    "axis_voltage": [...],
                    "load_rate": [...]
                },
                "counters": {
                    "counter_0": {"target": 3, "current": 0, "mode": 2}, ...
                }
            },
            "timestamp": "2025-06-26T22:43:14.512284Z"
        }
        """
        # 1. Datos en bloques (por límite de longitud del mensaje)
        querys = [
            ['isMoving','curAlarm','curMode','curCycle','lastCycle','curAccount','origin','RemoteCmdLen'],
            [f"axis-{i}" for i in range(8)],
            [f"world-{i}" for i in range(8)],
            [f"curTorque-{i}" for i in range(8)],
            [f"curSpeed-{i}" for i in range(8)],
            [f"Addr-{i}" for i in range(800, 850)],
            [f"Addr-{i}" for i in range(851, 890)]
        ]

        responses = []
        for i, query in enumerate(querys):
            msg = {
                "dsID": "www.hc-system.com.RemoteMonitor",
                "reqType": "query",
                "packID": str(1000 + i),
                "queryAddr": query
            }
            resp = self.send_json(msg)
            responses.append(resp.get("queryData", []))

        # 2. Entradas digitales
        x_bits = format(int(self.read_query("input-0")["queryData"][0]), '032b')[::-1]
        x_keys = [f"x{r}{c}" for r in range(1, 5) for c in range(8)]
        x_dict = {k: int(b) for k, b in zip(x_keys, x_bits)}

        # 3. Salidas digitales
        y_bits = format(int(self.read_query("output-0")["queryData"][0]), '032b')[::-1]
        y_keys = [f"y{r}{c}" for r in range(1, 5) for c in range(8)]
        y_dict = {k: int(b) for k, b in zip(y_keys, y_bits)}

        # 4. Memoria M
        m_bits = format(int(self.read_query("M-0")["queryData"][0]), '032b')[::-1]
        m_keys = [f"m{r}{c}" for r in [1,2,3,4,11,12,13,14] for c in range(8)]
        m_dict = {k: int(b) for k, b in zip(m_keys, m_bits)}

        # 5. Contadores
        counter_ids = self.read_query("counterList")["queryData"][0]
        counters = {}
        for cid in counter_ids:
            cdata = self.read_query(f"counter-{cid}")["queryData"][0]
            counters[f"counter-{cid}"] = {
                "id": cdata[0], "target": cdata[1], "current": cdata[2], "mode": 2
            }

        # 6. Ensamblar
        return {
            "robot_id": self.robot_id,
            "ip": self.host,
            "online": True,
            "status": {
                "order_id": None,
                "addresses": {
                    str(i + 800 if i < 50 else i + 801): int(v) for i, v in enumerate(responses[5] + responses[6])
                },
                "outputs": {
                    "x": x_dict,
                    "y": y_dict,
                    "m": m_dict,
                    "euy": {}  # si tienes otro bloque, agrégalo aquí
                },
                "status": {
                    "movement_status": [int(responses[0][0])],
                    "alarm_code": [int(responses[0][1])],
                    "cur_mode": [int(responses[0][2])],
                    "current_cycle_time": [float(responses[0][3])],
                    "last_cycle_time": [float(responses[0][4])],
                    "cur_account": [int(responses[0][5])],
                    "homed": [int(responses[0][6])],
                    # "cmd_lenght": [int(responses[0][7])],
                    "axis_position": [float(v) for v in responses[1]],
                    "world_position": [float(v) for v in responses[2]],
                    "axis_torque": [float(v) for v in responses[3]],
                    "axis_velocity": [float(v) for v in responses[4]]
                },
                "counters": counters
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }

    