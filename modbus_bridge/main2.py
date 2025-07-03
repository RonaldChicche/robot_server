import socket
import json

ROBOT_IP_01 = "192.168.100.20"
PORT = 9760

ROBOT_IP_02 = "192.168.101.22"
PORT = 9760

comando = {
  "dsID": "www.hc-system.com.RemoteMonitor",
  "reqType": "query",
  "packID": "0",
  "queryAddr": [
    "counterList",         # Lista de IDs de contadores
    "counter-0",
    "counter-1",           # Contador 1
    "counter-2", 
    "counter-3",           # Contador 0: [ID, target, current]
    "counter-4",           # Agrega más según necesidad
    "counter-8"
  ]
}

socket_borunte_01 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_borunte_01.connect((ROBOT_IP_01, PORT))
print("Robot 1 connected")
# socket_borunte_02 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# socket_borunte_02.connect((ROBOT_IP_02, PORT))
# print("Robot 2 connected")

while True:
    socket_borunte_01.sendall(json.dumps(comando).encode('utf-8'))
    respuesta = socket_borunte_01.recv(2048)
    print("Programas encontrados 01 : ", respuesta.decode())

    # socket_borunte_02.sendall(json.dumps(comando).encode('utf-8'))
    # respuesta = socket_borunte_02.recv(2048)
    # print("Programas encontrados 02 : ", respuesta.decode())
