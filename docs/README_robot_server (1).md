
# 🤖 robot_server

Arquitectura de servidor para líneas industriales con múltiples protocolos de comunicación. El sistema permite que los recursos como robots, PLCs y sensores puedan ser controlados y monitorizados mediante una API centralizada, con soporte para integración de servicios adicionales como dashboards, almacenamiento de métricas o analítica.

---

## 📚 Documentación Técnica

Toda la documentación técnica se encuentra dentro de la carpeta [`docs/`](./docs/). Aquí tienes un acceso directo a los principales módulos documentados:

- [01. Arquitectura General (Docker Compose)](docs/01_documentacion_general_docker_v2.md)
- [02. Configuración de Entorno y Variables](docs/02_configuracion_entorno.md)
- [03. Gateway de Robot Borunte (Socket)](docs/03_socket_gateway.md)
- [04. Flujo Node-RED para control de Borunte](docs/04_nodered_gateway.md)
- [05. Gateway Modbus TCP](docs/05_modbus_gateway.md)

---

## 📊 Diagrama General

![Diagrama](docs/images/robot_server.png)

---

## 🧩 Componentes Principales

- **OPC Gateway**: Extrae datos desde el PLC mediante protocolo OPC-UA.
- **Backend API**: Expone servicios para control externo y almacenamiento.
- **Frontend Web**: Visualización e interacción con recursos conectados.
- **Kafka**: Núcleo de mensajería del sistema para desacoplar el flujo de datos.
- **InfluxDB**: Base de datos temporal para registrar historial de estado y métricas.
- **Módulos Gateway**:
  - `socket_gateway`: Enlace TCP con robots Borunte.
  - `opc_gateway`: Enlace OPC-UA con PLCs.
  - `modbus_gateway`: Lectura y escritura sobre dispositivos Modbus TCP.

Todo el sistema está containerizado usando **Docker** para facilitar despliegue, portabilidad y mantenimiento.

---

## 📤 Kafka – Sistema de Mensajería

Kafka permite la comunicación asíncrona entre módulos desacoplados del sistema.

### Topics utilizados:

- **`robot.commands`**: Envía órdenes de ejecución.
- **`robot.status`**: Reporta estado actualizado.
- **`robot.responses`**: Respuestas a comandos.

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

---

## 📈 InfluxDB – Historización y Métricas

Todos los datos periódicos o eventos de estado se pueden registrar en **InfluxDB** para posterior análisis histórico o visualización en tiempo real (por ejemplo, mediante Grafana).

---

## 🔌 Comunicación con PLC (OPC-UA)

El **Gateway OPC-UA**, en contenedor Python, se conecta a un PLC vía OPC-UA para intercambio de datos de producción.

### Ejemplo de datos de entrada:

```json
{
  "device_id": "plc_01",
  "position": {"x": 125.0, "y": 38.0, "z": 2.5},
  "running": true,
  "alarm_code": 103,
  "timestamp": "2025-07-18T14:05:00Z"
}
```

---

## 🤖 Comunicación con Robots Borunte (TCP)

Cada `Robot Gateway` se conecta mediante socket TCP con un robot Borunte.

- Recibe comandos estructurados (JSON serializado).
- Devuelve estado estructurado periódicamente.
- Identifica cada robot por `robot_id` (ej. `"01"`, `"02"`).
