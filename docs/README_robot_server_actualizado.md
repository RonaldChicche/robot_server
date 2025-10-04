
# 🤖 robot_server

Arquitectura de servidor para líneas industriales con múltiples protocolos de comunicación. El sistema permite que los recursos como robots, PLCs y sensores puedan ser controlados y monitorizados mediante una API centralizada, con soporte para integración de servicios adicionales como dashboards, almacenamiento de métricas o analítica.

---

## 📚 Documentación Técnica

La documentación detallada de cada módulo se encuentra en la carpeta [`docs/`](./docs/):

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

- **Node-RED Gateway**: Controla al robot Borunte mediante tramas TCP específicas usando lógica visual.
- **Modbus Bridge**: Traduce y ejecuta comandos sobre un dispositivo Modbus esclavo (simulando un PLC).
- **Modbus Slave**: Expone registros para recibir y entregar datos del sistema principal hacia el PLC real.
- **Backend API**: Provee servicios HTTP para monitoreo y control centralizado.
- **Frontend Web**: Interfaz gráfica para usuarios y operadores (React).
- **Kafka**: Sistema de mensajería asíncrona para conectar todos los módulos.
- **InfluxDB**: Almacena métricas y estados de producción históricos.

Todo el sistema está containerizado usando **Docker** para facilitar despliegue, portabilidad y mantenimiento.

---

## 📤 Kafka – Sistema de Mensajería

Kafka permite la comunicación desacoplada entre módulos del sistema.

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

## 🔁 Comunicación con PLC (Modbus TCP)

El sistema se conecta con el PLC mediante un módulo **Modbus Slave** que expone registros simulados. El módulo `modbus_gateway` funciona como puente traductor:

- Lee periódicamente bloques de registros (`read_holding_registers`, `read_coils`).
- Escribe en registros y bobinas según comandos recibidos.

Esto permite interacción directa con sistemas PLC compatibles con Modbus.

---

## 🤖 Control de Robots Borunte (vía Node-RED)

El control de los robots Borunte se realiza mediante un flujo Node-RED que:
- Interpreta comandos del sistema y los traduce a tramas TCP válidas para el robot.
- Recibe estado en tiempo real desde el robot.
- Administra FSM (máquina de estados) para cada proceso.
- Realiza escrituras sobre posiciones, bits y configuraciones de proceso en la memoria del robot.

