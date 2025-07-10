# robot_server
Arquitectura de servidor para lineas con varios protocolos de comunicacion. El objetivo es conseguir que estos recursos puedan ser manejados y consultados mediante una API para mayor flexibilidad, ademas de proporcionar una puerta a integrar mas servicios y caracteristicas como una visualizacion

## Diagrama
![Diagrama](docs/images/robot_server.png)

## 🔧 Componentes Principales

- **Coordinador**: Administra instrucciones leídas de Redis y envía nuevas órdenes.
- **Command Listener**: Consume comandos desde Kafka y los publica en Redis.
- **Status Listener**: Lee estados desde Redis y los publica en Kafka.
- **Robot Gateway**: Interfaz socket con los robots Borunte (lectura de estado + ejecución de comandos).

Todo el sistema está dockerizado para facilitar el despliegue y mantenimiento.


## 📤 Kafka

Kafka es el núcleo del sistema de mensajería. Permite la comunicación desacoplada entre módulos como `command-listener`, `status-listener` y `robot-gateway`.

#### Topics utilizados:

- `robot.commands`: Recibe órdenes para los dispositivos.
- `robot.status`: Publica el estado actual de los robots o PLCs.
- `robot.responses`: Envía respuestas a comandos ejecutados.

Cada mensaje es un JSON estructurado que puede incluir datos como `order_id`, `target_id`, parámetros del proceso, y marcas de tiempo.

## 📈 InfluxDB

Todos los datos de estado y métricas de los robots se pueden almacenar en **InfluxDB** para análisis histórico o visualización en dashboards (por ejemplo, Grafana).




<!-- ---

## 🔁 Comunicación con PLC

### 📥 Datos recibidos del PLC
```json
{
  "device_id": "robot1",
  "position": {"x": 123.4, "y": 456.7, "z": 789.0},
  "running": true,
  "alarm_code": 104,
  "timestamp": "2025-06-24T12:34:56Z"
}
```

## Para PLC 
- Recibe
{
  "device_id": "robot1",
  "position": {"x": 123.4, "y": 456.7, "z": 789.0},
  "running": true,
  "alarm_code": 104,
  "timestamp": "2025-06-24T12:34:56Z"
}

-manda
{
  "order_id": "ORD_1001",
  "target_device": "robot1",
  "type": "method",
  "name": "process_01",
  "params": {
    "quantity": 5,
    "dx": 1.2,
    "dy": -0.3,
    "dz": 0.0,
    "speed": 1200
  }
}

# Estructura del mensaje:
# robot.commands
# {
#     "order_id": "ORD_20230626123456_borunte_01",
#     "target_id": "borunte_01",
#     "type": "method",
#     "name": "set_output",
#     "params": ["y13", 1]
# }

# robot.status
# {
#     "target_id": "borunte_01",
#     "ip": "127.0.0.1",
#     "online": true,
#     "status": {
          "order_id": "...",
#         "y13": 1
#     },
#     "timestamp": "2023-06-26T12:34:56.789Z"
# }

# robot.responses
# {
#     "target_id": "borunte_01",
#     "type": "method",
#     "online": True,
#     "command": method_name,
#     "result": {"status": True, ...},
#     "error": None,
#     "timestamp": "2023-06-26T12:34:56.789Z"
# } -->