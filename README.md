# robot_server

Arquitectura de servidor para líneas industriales con múltiples protocolos de comunicación. El sistema permite que los recursos como robots, PLCs y sensores puedan ser controlados y monitorizados mediante una API centralizada, con soporte para integración de servicios adicionales como dashboards, almacenamiento de métricas o analítica.

## 📊 Diagrama General

![Diagrama](docs/images/robot_server.png)

## 🧩 Componentes Principales

- **Cliente OPC**: Extrae datos desde el PLC mediante protocolo OPC-UA.
- **Backend API**: Expone servicios para control externo y almacenamiento (Express.js + PostgreSQL).
- **Frontend**: Visualización e interacción con los recursos conectados (React).
- **Kafka**: Núcleo de mensajería del sistema para desacoplar el flujo de datos.
- **InfluxDB**: Base de datos temporal para registrar el historial de estado y métricas de robots.
- **Módulos Dockerizados**:
  - `Coordinator`: Orquesta las acciones internas del sistema leyendo comandos desde Redis.
  - `Command Listener`: Escucha órdenes desde Kafka (`robot.commands`) y las envía a Redis.
  - `Status Listener`: Publica en Kafka el estado leído desde Redis (`robot.status`).
  - `Robot Gateway (01, 02)`: Conectores socket que comunican con los robots Borunte (envían y reciben comandos/estado).

Todo el sistema está containerizado usando **Docker** para facilitar despliegue, portabilidad y mantenimiento.

## 📤 Kafka – Sistema de Mensajería

Kafka permite la comunicación asíncrona entre módulos desacoplados del sistema.

### Topics utilizados:

- **`robot.commands`**: Envía órdenes de ejecución a robots o PLCs.
- **`robot.status`**: Reporta el estado actualizado de los dispositivos.
- **`robot.responses`**: Respuestas a comandos, incluyendo resultado y errores.

### Ejemplo de mensaje – `robot.commands`:
```json
{
  "order_id": "ORD_1001",
  "target_id": "robot_01",
  "type": "method",
  "name": "set_output",
  "params": ["y13", 1],
  "timestamp": "2025-07-18T14:00:00Z"
}
```

## 📈 InfluxDB – Historización y Métricas

Todos los datos periódicos o eventos de estado se pueden registrar en **InfluxDB** para posterior análisis histórico o visualización en tiempo real (por ejemplo, mediante Grafana).

## 🔌 Comunicación con PLC (OPC-UA)

El **Cliente OPC**, en contenedor Python, se conecta a un PLC vía OPC-UA para intercambiar datos de producción.

### Datos de entrada:
```json
{
  "device_id": "plc_01",
  "position": {"x": 125.0, "y": 38.0, "z": 2.5},
  "running": true,
  "alarm_code": 103,
  "timestamp": "2025-07-18T14:05:00Z"
}
```

## 🤖 Comunicación con Robots (vía Socket)

Cada `Robot Gateway` conecta con un robot Borunte mediante un socket TCP:
- Recibe comandos estructurados.
- Devuelve estado y confirmaciones.
- Cada robot se identifica por un `target_id`.