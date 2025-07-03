import socket
import json

# Dirección IP y puerto del servidor (ajusta si usas contenedor separado)
HOST = 'localhost'
PORT = 9700

# Ejemplo de mensaje tipo query
query_message = {
    "dsID": "www.hc-system.com.RemoteMonitor",
    "reqType": "query",
    "packID": "123",
    "queryAddr": ["version", "curMold", "curMode"]
}

# Convierte a string JSON
data_to_send = json.dumps(query_message)

# Conexión TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(data_to_send.encode())
    response = s.recv(4096)

print("🧾 Respuesta del servidor:")
print(response.decode())
