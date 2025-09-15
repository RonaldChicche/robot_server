
# 🔌 Módulo Modbus Gateway – Lectura y Escritura Modbus TCP

Este módulo actúa como puente de comunicación entre el sistema principal y un dispositivo o simulador Modbus TCP (esclavo). Se encarga de generar lecturas periódicas y ejecutar escrituras selectivas en registros Modbus.

---

## 🧩 Estructura del módulo

```plaintext
modbus_gateway/
├── ModbusClient.py      # Clase cliente para conexión Modbus TCP
├── reader.py            # Script que realiza lecturas periódicas
├── runner.py            # Punto de entrada principal del servicio
├── config.yaml          # Configuración de las direcciones y registros a usar
├── Dockerfile           # Imagen del servicio
```

---

## ⚙️ Funcionamiento General

- El cliente Modbus se conecta a un **servidor Modbus TCP esclavo** configurado en `config.yaml`
- Realiza lecturas periódicas de múltiples bloques (`read_holding_registers`, `read_coils`)
- Permite escritura de datos en registros específicos (`write_register`, `write_registers`, `write_coil`)
- Las operaciones están estructuradas como comandos JSON que definen el tipo de operación, dirección, valores, etc.

---

## 📥 Tramas de entrada (Comandos esperados)

El módulo recibe comandos como objetos JSON con las siguientes estructuras:

### ✅ Lectura de registros

```json
{
  "op": "read",
  "type": "holding",
  "address": 100,
  "length": 10
}
```

- `op`: `"read"` indica operación de lectura
- `type`: `"holding"` (otros: `"coil"`, `"input"`, `"discrete"`)
- `address`: dirección base a leer
- `length`: cantidad de registros

---

### ✍️ Escritura de un solo registro

```json
{
  "op": "write",
  "type": "register",
  "address": 200,
  "value": 1234
}
```

---

### ✍️ Escritura de múltiples registros

```json
{
  "op": "write",
  "type": "registers",
  "address": 300,
  "values": [10, 20, 30]
}
```

---

### ✍️ Escritura de bobina

```json
{
  "op": "write",
  "type": "coil",
  "address": 5,
  "value": true
}
```

---

## 📤 Tramas de respuesta

Las respuestas siguen el mismo patrón, devolviendo los valores obtenidos o el resultado de la operación:

### Ejemplo respuesta de lectura

```json
{
  "status": "ok",
  "address": 100,
  "type": "holding",
  "values": [1024, 2048, 4096]
}
```

### Ejemplo respuesta de error

```json
{
  "status": "error",
  "error": "Connection refused"
}
```

---

## 🛠️ Configuración (`config.yaml`)

El archivo `config.yaml` define los bloques que serán leídos periódicamente:

```yaml
modbus:
  host: 190.168.10.20
  port: 5020
  unit_id: 1

polling:
  interval_ms: 1000
  blocks:
    - name: status_block
      type: holding
      address: 800
      length: 20
    - name: outputs
      type: coil
      address: 0
      length: 16
```

---

## 🔄 Ejecución cíclica

El script `reader.py` ejecuta lecturas cada `interval_ms` milisegundos, acumulando respuestas por bloque, y enviándolas a una interfaz superior (no cubierta aquí).

---

## 🧾 Observaciones

- El módulo implementa directamente funciones estándar Modbus:
  - FC03 (`read_holding_registers`)
  - FC01 (`read_coils`)
  - FC05 (`write_single_coil`)
  - FC06 (`write_single_register`)
  - FC16 (`write_multiple_registers`)
- Usa una clase `ModbusClient` que encapsula reconexión, logs y acceso seguro.
- La conexión es robusta y maneja reintentos si el esclavo no responde.

