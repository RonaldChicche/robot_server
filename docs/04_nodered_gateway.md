
# 🔌 Módulo Node-RED para Control de Robot Borunte

Este flujo Node-RED reemplaza al cliente TCP en Python para el control del robot Borunte. Se encarga de enviar tramas, recibir estados, administrar FSMs (máquina de estados), y operar sobre memoria de trabajo del robot a través de TCP y Redis.

---

## 🧠 1. Funcionamiento General

- El nodo central `tcp-client` se conecta al robot Borunte usando una interfaz por sockets (`ROBOT_HOST`, `ROBOT_PORT`).
- Los comandos y procesos se envían a través del buffer `robot:{id}:cmd_buffer` (en Redis) como estructuras JSON que se traducen a tramas específicas del protocolo HC-System.
- Cada comando enviado genera una o varias tramas JSON codificadas y serializadas como string.
- Los estados del robot son leídos periódicamente (cada 1 s) mediante un conjunto de 11 requests (`packID 1000–1010`) que consultan distintas áreas de memoria del robot.
- Las respuestas se ensamblan y almacenan en `robot:{id}:sensor_data`.

---

## 🧾 2. Estructura de las Tramas Enviadas

Las tramas siguen el siguiente formato:

```json
{
  "dsID": "www.hc-system.com.RemoteMonitor",
  "reqType": "command",
  "packID": "900001",
  "cmdData": ["startButton"]
}
```

### Comandos simples (`cmdData`):
- `["startButton"]`
- `["stopButton"]`
- `["actionPause"]`
- `["actionStop"]`
- `["modifyOutput", 0, yIndex, value]` → Para prender o apagar salidas Y
- `["rewriteData", address, value, permanent]`
- `["rewriteDataList", start_addr, length, permanent, ...data]`

### Comandos de proceso como `proceso_01` generan hasta **10 tramas**:
1. Activación con `rewriteData(850, 1)`
2. Reset de contadores `rewriteData(855, 0)`
3. Escritura de vectores `pick`, `put`, `up`, `down`, `pick_up` (bloques de 6 posiciones)
4. Configuración en `820`: cantidades, desplazamientos, espesores, bits
5. Configuración en `851–852`: compensaciones

---

## 📦 3. Datos de Memoria del Robot

### 📍 Direcciones de memoria

| Dirección | Uso                                |
|----------:|-------------------------------------|
| 800–805   | Posiciones PICK (X, Y, Z...)        |
| 810–815   | Posiciones PLACE                    |
| 820[0]    | cantidad_z                          |
| 820[1]    | cantidad_x                          |
| 820[2–3]  | desplazamientos dz_p y dz_n         |
| 820[4–5]  | espesor, ancho                      |
| 820[6]    | dz_pick                             |
| 820[7]    | bit_coordinador                     |
| 820[8]    | compensación en X                   |
| 830–835   | Desplazamiento hacia arriba         |
| 840–845   | Desplazamiento hacia abajo          |
| 851       | bit_compensación                    |
| 852       | compensación de desfase             |
| 855       | Reset de contadores (valor 0)       |
| 860–865   | Movimiento de PICK-UP               |
| 872       | Compensación Z (en `proceso_05`)    |

---

### 🔘 Bits de salida (Y)

| Salida Y | Descripción                       |
|----------|-----------------------------------|
| Y10      | Fin de ciclo                      |
| Y33      | Fin de proceso                    |
| Y30/Y32  | Cancelación de rutina             |
| Y35/Y36  | Apagado forzado                   |
| Y45      | Movimiento coordinado (ON/OFF)    |
| Y20–Y27  | Uso general                        |
| Y40–Y47  | Uso general                        |

---

## 🧠 4. Máquina de Estados (FSM)

El flujo incluye una FSM global que mantiene el estado de proceso, con transiciones según comandos y señales digitales:

| Estado      | Transición desde                    |
|-------------|-------------------------------------|
| `Vacio`     | Inicial o tras reset                |
| `Running`   | Al iniciar proceso (`startButton`)  |
| `Paused`    | `actionPause`, si está corriendo    |
| `Stopped`   | `stopButton` o error (alarm != 0)   |
| `Terminated`| Si `Y10` y `Y33` están activos       |

> Si `Stopped` y no hay alarma: vuelve a `Vacio`.

---

## 📤 5. Datos leídos desde el robot

Cada 1 segundo se envían 11 bloques de request (`packID 1000–1010`). Se consulta:

| packID | Información                             |
|--------|------------------------------------------|
| 1000   | isMoving, alarm, modo, ciclos, homing   |
| 1001   | Posición por ejes (`axis-0` a `axis-7`) |
| 1002   | Posición cartesiana (`world-0` a `world-7`) |
| 1003   | Torque actual de cada eje               |
| 1004   | Velocidad actual                        |
| 1005   | Dirección 800–849 (50 datos)            |
| 1006   | Dirección 851–889 (39 datos)            |
| 1007   | Entradas digitales (`input-0`)          |
| 1008   | Salidas digitales (`output-0`)          |
| 1009   | Marcadores (`M-0`)                      |
| 1010   | Contadores (id, target, current)        |

> Los datos se ensamblan en un objeto JSON y se publican en `robot:{id}:sensor_data`.

---

## 🔄 6. Comunicación Redis

| Clave Redis                     | Uso                                 |
|----------------------------------|--------------------------------------|
| `robot:{id}:cmd_buffer`        | Donde se escuchan los comandos       |
| `robot:{id}:cmd_result`        | Respuesta de cada comando enviado    |
| `robot:{id}:sensor_data`       | Datos de estado ensamblados          |
| `robot:{id}:connected`         | TTL renovado cada 3 s si conectado   |
| `process:state`                | Estado actual del proceso (FSM)      |

---

## 🧾 7. Ejemplo de ejecución `proceso_01`

1. Se escribe `850 = 1`, `855 = 0` (iniciar y reset)
2. Se cargan listas:
   - `800–805` → `pick`
   - `810–815` → `put`
   - `830–835` → `up`
   - `840–845` → `down`
   - `860–865` → `pick_up`
3. Se escribe configuración en `820` y `851–852`
4. Se llama `startButton`
5. FSM transiciona a `Running`

---

## ✅ Observaciones Finales

- Toda la interacción está desacoplada: Redis para comandos/estados, TCP para envío/recepción.
- Cada comando genera una o varias tramas independientes que siguen el protocolo HC-System.
- Node-RED controla estado, salida digital, y comunicación a través de buffers centralizados.

