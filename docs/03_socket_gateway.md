
# 🔌 Módulo: Socket Gateway

Este módulo orquesta la interacción con robots industriales Borunte mediante comunicación TCP, utilizando sockets. Aunque la clase `JsonBorunteClient` está presente, su uso ha sido reemplazado temporalmente por flujos en Node-RED. Aun así, los demás scripts del módulo siguen activos y utilizan Redis como mecanismo de intercambio de datos y control de flujo.

---

## 🧩 Estructura General

```plaintext
socket_gateway/
├── command_listener.py
├── gateway_robot.py
├── process_coordinator.py
├── status_listener.py
├── JsonBorunteClient.py       # (desactivado)
├── common/
│   ├── redis_keys.yaml        # Definición de claves Redis
│   └── utils.py               # Funciones auxiliares
```

---

## ⚙️ Descripción por script

### 1. `gateway_robot.py`
- Script principal que coordina el proceso.
- Encapsula la lógica de producción.
- Orquesta llamadas a funciones del coordinador (`process_coordinator`) y listeners.
- No expone claves de Redis directamente, delega a helpers y configuraciones externas.

### 2. `process_coordinator.py`
- Encargado de gestionar el flujo de producción: iniciar, detener, continuar.
- Realiza cálculos de posiciones (X pick, X place, Z place) usando:
  - Ancho (`self.ancho_scaled`)
  - Espesor (`self.espesor_scaled`)
  - Contadores (`self.counters["counter-0"]["current"]`, etc.)
- **Coordenadas escritas al robot (vía cliente o proxy):**
  - `800-805` → `XYZ Pick`
  - `810-815` → `XYZ Place`
- **Bits de control activados (vía robot):**
  - `850` → `Bit Switch del proceso`
  - `855` → `Recuperacion proceso con contadores`
  - `Y45`  → `Activación de movimiento del robot desde el punto de espera`

### 3. `command_listener.py`
- Escucha comandos desde Kafka o Redis.
- Traduce comandos de texto (`START`, `STOP`, etc.) en señales para Redis.
- Empuja comandos al buffer del robot (`robot:{id}:cmd_buffer`)
- Publica resultados en: `robot:{id}:cmd_result` y `process:log`

### 4. `status_listener.py`
- Lee el estado de los robots Borunte.
- Publica en Kafka (`robot_status`) y Redis (`robot:{id}:status`)
- Actualiza datos de sensores, IO, y posición de ejes (`joint_pos`).
- Usa plantillas dinámicas para múltiples robots (`{id}`)

### 5. `JsonBorunteClient.py` (no activo)
- Cliente de socket para enviar/recibir tramas a robots Borunte.
- Envía coordenadas a direcciones numéricas (ej. 800, 810...).
- Reemplazado por lógica en Node-RED actualmente.

---

## 🧠 Redis Key Definitions (`redis_keys.yaml`)

El archivo `redis_keys.yaml` define la estructura y plantilla de claves Redis utilizadas por cada componente.

### ✳️ General: `gateway_template`
```yaml
robot:{id}:status
robot:{id}:log
robot:{id}:connected
robot:{id}:robot_enabled
robot:{id}:cmd_buffer
robot:{id}:cmd_result
robot:{id}:sensor_data
robot:{id}:error
robot:{id}:start_button
robot:{id}:pause_button
robot:{id}:stop_button
```

### 📥 `command_listener`
```yaml
command:status
command:log
kafka:robot_commands
robot:{id}:cmd_buffer
robot:{id}:cmd_result
process:buffer
process:state
process:log
```

### 📤 `status_listener`
```yaml
status_listener:log
kafka:robot_status
process:status
robot:{id}:connected
robot:{id}:sensor_data
robot:{id}:cmd_result
robot:{id}:joint_pos
robot:{id}:io
```

### ⚙️ `process_coordinator`
```yaml
process:status
process:log
process:buffer
process:state
process:current
process:result
process:order_id
process:name
process:params
process:{id}:status
robot:{id}:cmd_buffer
robot:{id}:robot_enabled
robot:{id}:last_result
process:{id}:state
process:{id}:next_action
process:{id}:assigned_robot
process:{id}:override
```

---

## 🔁 Interfaz de Control (entre servicios)

Todos los servicios del módulo interactúan con Redis usando plantillas de clave con `robot:{id}`, lo que permite manejar múltiples robots y procesos simultáneamente.

---

## ⚠️ Observación

Aunque el cliente directo por socket está desactivado, los scripts conservan compatibilidad con la estructura original. Esto permite reactivar `JsonBorunteClient` fácilmente si se requiere en el futuro.

