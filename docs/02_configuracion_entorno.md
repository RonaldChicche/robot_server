
# ⚙️ Configuración del Entorno y Diseño de Comunicación

Este documento complementa la arquitectura general del sistema con detalles clave de configuración definidos en variables de entorno y en archivos técnicos de diseño de comunicación.

---

## ✅ Variables de Entorno (.env)

El archivo `.env` define las variables necesarias para levantar y coordinar todos los servicios del sistema. A continuación se presenta un resumen organizado por categorías.

### 🟦 Kafka

- **Broker interno**: `kafka:29092`
- **Broker expuesto**: `<IP-host>:9092`
- **Tópicos usados**:
  - `robot.commands`
  - `robot.status`
  - `robot.responses`

### 🟥 Redis

- **Host**: `127.0.0.1`
- **Puerto**: `6379`

### 🟨 Robots Borunte (Socket)

- `BORUNTE_01` → IP: `190.168.10.32`, puerto: `9761`
- `BORUNTE_02` → IP: `190.168.10.31`, puerto: `9761`
- Intervalo de actualización de estado: `3 segundos` (`STATUS_INTERVAL`)

### 🟫 PostgreSQL

- **Host**: `host.docker.internal`
- **Puerto**: `5432`
- **Base de datos**: `robot_config`
- **Usuario**: `robotadmin`

### 🟩 Otros Servicios

| Servicio   | Puerto | Descripción                  |
|------------|--------|------------------------------|
| Backend    | 8000   | API central de lógica        |
| Frontend   | 80   | Interfaz de usuario web      |
| PGAdmin    | 5050   | Panel administrativo de DB   |
| Modbus     | 5020   | Puerto de comunicación TCP   |

---

## 📑 Diseño de Trama OPC-UA (`OPC IO.xlsx`)

El archivo Excel entregado contiene una tabla de nodos utilizados para la lectura y escritura de datos a través de OPC-UA. Incluye:

- Direcciones completas de nodos (`NodeId`)
- Variables relacionadas al estado de máquinas o robots
- Posibles mapeos hacia los tópicos de Kafka

**Próximo paso:** Se puede generar una tabla con estos nodos para ser incluida como documentación técnica de referencia del Gateway OPC.

---
