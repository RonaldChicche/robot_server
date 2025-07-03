
import socket
import json

class JSONBorunteClient:
    def __init__(self, host='127.0.0.1', target_id="borunte_test_01", port=9760, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.target_id = target_id
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), self.timeout)

    def disconect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send_json(self, data):
        if not self.sock:
            self.connect()
        message = json.dumps(data)
        self.sock.sendall(message.encode('utf-8'))


        response = b""
        while not response.endswith(b'}'):
            chunk = self.sock.recv(2048)
            if not chunk:
                break
            response += chunk

        return json.loads(response.decode('utf-8').strip())

    def read_query(self, keys, pack_id="1"):
        request = {
            "dsID": "www.hc-system.com.RemoteMonitor",
            "reqType": "query",
            "packID": pack_id,
            "queryAddr": [keys]
        }
        print(f"Sending request: {request}")
        return self.send_json(request)

    def send_command(self, cmd_array, pack_id="1"):
        cmd_array = [*map(str, cmd_array)]
        request = {
            "dsID": "www.hc-system.com.RemoteMonitor",
            "reqType": "command",
            "packID": pack_id,
            "cmdData": cmd_array
        }
        print(f"Sending request: {request}")
        return self.send_json(request)

    def modify_counter(self, counter_id, current, target):
        cmd_array = ["modifyCounter", counter_id, current, target] 
        return self.send_command(cmd_array, "1")
    
    def modify_stack(self, stack_id, X, Y, Z, x_count, y_count, z_count):
        cmd_array = ["modifyStack", stack_id, X, Y, Z, x_count, y_count, z_count]
        return self.send_command(cmd_array, "1")
    
    def modify_global_velocity(self, velocity):
        cmd_array = ["modifyGSPD", velocity*10]
        return self.send_command(cmd_array, "1")

    def write_data_single(self, addres: int, value: int, permanent: int=0):
        cmd_array = ["rewriteData", addres, value, permanent]
        return self.send_command(cmd_array, "1")
    
    def write_data_block(self, start_address: int, data: list[int], permanent: int=0):
        cmd_array = ["rewriteDataList", start_address, len(data), permanent, *data]
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

    def proceso_01(self, data: dict):
        """
        Proceso 1: paletizado frontal con ajuste XY, cantidad, altura de stack y velocidad.
        Args:
            data (dict): {
                "pick": [x, y, z, rx, ry, rz],
                "put": [x, y, z, rx, ry, rz],
                "cantidad": int,
                "dx": float,
                "dy": float,
                "altura": float,
                "velocidad": int
            }
        Returns:
            dict: Resultados de verificación
        """
        required_keys = ["pick", "put", "cantidad", "dx", "dy", "altura", "velocidad"]
        
        pick_scaled = [int(i * 1000) for i in data["pick"]]
        put_scaled = [int(i * 1000) for i in data["put"]]

        self.write_data_block(800, pick_scaled)
        self.write_data_block(810, put_scaled)

        compe = (data["cantidad"] - 1) * data["altura"]
        self.write_data_block(820, [
            int(data["dx"]*1000), int(data["dy"]*1000),
            int(compe*1000), data["altura"]*1000,
            data["cantidad"], data["velocidad"]
        ])

        self.modify_global_velocity(data["velocidad"])
        return True

    def query_all_borunte_data(self):
        """
        {
            "target_id": "borunte_test_02",
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

        pass

    def generar_request_status_completo(self, pack_id="1"):
        return {
            "dsID": "www.hc-system.com.RemoteMonitor",
            "reqType": "query",
            "packID": pack_id,
            "queryAddr": (
                [str(i) for i in range(800, 850)] +
                [
                    "movement_status", "home_status", "alarm_code", "global_velocity",
                    "current_cycle_time", "last_cycle_time", "axis_temperature",
                    "axis_position", "world_position", "axis_velocity", "axis_torque",
                    "axis_voltage", "load_rate", "counter_0", "counter_1", "counter_2"
                ] +
                [f"y{r}{c}" for r in range(1, 5) for c in range(0, 8)] +
                [f"m{r}{c}" for r in [1,2,3,4,11,12,13,14] for c in range(0, 8)] +
                [f"m1{r}" for r in range(10, 50)] +
                [f"euy{r}{c}" for r in range(1, 5) for c in range(0, 8)]
            )
        }