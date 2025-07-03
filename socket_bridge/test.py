from JsonBorunteClient import JSONBorunteClient
import socket, json, time

client = JSONBorunteClient("192.168.100.20", "default")

# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect()
# client = socket.create_connection(("192.168.100.20", 9760), 5)

command = {
    "dsID": "www.hc-system.com.RemoteMonitor",
    "reqType": "command",
    "packID": "0",
    "cmdData": ["startButton"]
}

query = {
    "dsID": "www.hc-system.com.RemoteMonitor",
    "reqType": "query",
    "packID": "0",
    "queryAddr": ["counterList"]
}


try: 
    print("✅ Conectado")
    response = client.stop_button()
    print("RESPONSE: ", response)
except Exception as e:
    print("❌ ERROR: ", e)
    print(e)

