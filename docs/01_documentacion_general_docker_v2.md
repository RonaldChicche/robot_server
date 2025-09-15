
# 🧱 Arquitectura General del Sistema (Docker Compose)

Este sistema está compuesto por múltiples servicios definidos en un archivo Docker Compose. Cada contenedor cumple un rol específico dentro del entorno, ya sea en la gestión de datos, la interfaz gráfica o la comunicación con dispositivos industriales.

---

## 🧩 Resumen de Servicios

| Servicio             | Función Principal (estimada)                                                      |
|----------------------|------------------------------------------------------------------------------------|
| **backend**          | Expone una API REST que envia mensajes a kafka para dar comandos   |
| **frontend**         | Interfaz web para usuarios                                                         |
| **modbus_slave**     | Dispositivo esclavo Modbus TCP                                       |
| **redis**            | Almacenamiento en memoria para intercambio rápido de datos entre servicios |
| **postgres**         | Base de datos relacional                                                           |
| **nodered**          | Plataforma de flujos lógicos para automatización o integración                    |
| **kafka**            | Sistema de mensajería para comunicación asincrónica                               |
| **kafka-ui**         | Interfaz web para monitorear el broker Kafka                                      |

---

## 📡 Puertos Expuestos

| Servicio      | Puerto Local | Descripción                        |
|---------------|--------------|------------------------------------|
| frontend      | 80         | Interfaz web                       |
| backend       | 5000         | API de backend                     |
| modbus_slave  | 5020         | Servidor Modbus TCP                |
| redis         | 6379         | Puerto estándar Redis              |
| postgres      | 5432         | Puerto PostgreSQL                  |
| kafka-ui      | 8080         | Interfaz de administración Kafka   |
| kafka         | 9092         | Puerto estándar para Kafka         |

---

## 🔧 Observaciones

- Los servicios están distribuidos en una misma red Docker interna para facilitar la comunicación.
- El sistema incluye tanto bases de datos como herramientas de comunicación industrial.
- La arquitectura es modular y escalable.

