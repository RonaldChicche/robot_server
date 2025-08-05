CREATE TABLE methods (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  type TEXT NOT NULL,           -- Ejemplo: 'method', 'proceso'
  description TEXT,
  requires_params BOOLEAN DEFAULT false
);



CREATE TABLE parameters (
  id SERIAL PRIMARY KEY,
  method_id INTEGER NOT NULL REFERENCES methods(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  type TEXT NOT NULL,           -- Ejemplo: 'int', 'float', 'bool', 'list'
  required BOOLEAN DEFAULT false,
  default_value TEXT,
  group_name TEXT,              -- Para agrupar campos como pick/put
  param_order INTEGER           -- Para indicar el orden en el comando
);


INSERT INTO methods (name, type, description, requires_params) VALUES
  ('start_button', 'method', 'Inicia el robot', false),
  ('stop_button_single', 'method', 'Detiene el robot (simple)', false),
  ('stop_button', 'method', 'Acción de parada', false),
  ('pause_button', 'method', 'Pone en pausa el robot', false),
  ('clear_alarm_button', 'method', 'Limpia las alarmas', false),
  ('clear_alarm_run_next', 'method', 'Limpia alarmas y ejecuta siguiente paso', false),
  ('clear_alarm_and_continue', 'method', 'Limpia alarmas y continúa la ejecución', false),
  ('modify_counter', 'method', 'Modifica un contador específico', true),
  ('modify_stack', 'method', 'Modifica una pila con posiciones', true),
  ('modify_global_velocity', 'method', 'Modifica la velocidad global del robot', true),
  ('write_data_single', 'method', 'Escribe un dato en una dirección específica', true),
  ('write_data_block', 'method', 'Escribe un bloque de datos en múltiples direcciones', true),
  ('proceso_01', 'proceso', 'Proceso completo de colocación', true),
  ('proceso_02', 'proceso', 'Proceso alternativo 2', true),
  ('proceso_03', 'proceso', 'Proceso alternativo 3', true),
  ('modify_output_y', 'method', 'Modifica una salida Y', true);



INSERT INTO parameters (method_id, name, type, required)
VALUES
((SELECT id FROM methods WHERE name = 'modify_counter'), 'counter_id', 'integer', true),
((SELECT id FROM methods WHERE name = 'modify_counter'), 'current', 'integer', true),
((SELECT id FROM methods WHERE name = 'modify_counter'), 'target', 'integer', true);


INSERT INTO parameters (method_id, name, type, required)
VALUES
((SELECT id FROM methods WHERE name = 'modify_stack'), 'stack_id', 'integer', true),
((SELECT id FROM methods WHERE name = 'modify_stack'), 'X', 'float', true),
((SELECT id FROM methods WHERE name = 'modify_stack'), 'Y', 'float', true),
((SELECT id FROM methods WHERE name = 'modify_stack'), 'Z', 'float', true),
((SELECT id FROM methods WHERE name = 'modify_stack'), 'x_count', 'integer', true),
((SELECT id FROM methods WHERE name = 'modify_stack'), 'y_count', 'integer', true),
((SELECT id FROM methods WHERE name = 'modify_stack'), 'z_count', 'integer', true);

INSERT INTO parameters (method_id, name, type, required)
VALUES
((SELECT id FROM methods WHERE name = 'modify_global_velocity'), 'velocity', 'integer', true);

INSERT INTO parameters (method_id, name, type, required)
VALUES
((SELECT id FROM methods WHERE name = 'write_data_single'), 'address', 'integer', true),
((SELECT id FROM methods WHERE name = 'write_data_single'), 'value', 'integer', true),
((SELECT id FROM methods WHERE name = 'write_data_single'), 'permanent', 'integer', false);

INSERT INTO parameters (method_id, name, type, required)
VALUES
((SELECT id FROM methods WHERE name = 'write_data_block'), 'start_address', 'integer', true),
((SELECT id FROM methods WHERE name = 'write_data_block'), 'data', 'list[integer]', true),
((SELECT id FROM methods WHERE name = 'write_data_block'), 'permanent', 'integer', false);

INSERT INTO parameters (method_id, name, type, required, default_value, group_name, param_order)
VALUES
((SELECT id FROM methods WHERE name = 'proceso_01'), 'pick_x', 'float', true, null, 'pick', 1),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'pick_y', 'float', true, null, 'pick', 2),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'pick_z', 'float', true, null, 'pick', 3),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'pick_rx', 'float', true, null, 'pick', 4),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'pick_ry', 'float', true, null, 'pick', 5),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'pick_rz', 'float', true, null, 'pick', 6),

((SELECT id FROM methods WHERE name = 'proceso_01'), 'put_x', 'float', true, null, 'put', 1),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'put_y', 'float', true, null, 'put', 2),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'put_z', 'float', true, null, 'put', 3),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'put_rx', 'float', true, null, 'put', 4),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'put_ry', 'float', true, null, 'put', 5),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'put_rz', 'float', true, null, 'put', 6),

((SELECT id FROM methods WHERE name = 'proceso_01'), 'cantidad_z', 'integer', true, null, null, 1),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'cantidad_x', 'integer', true, null, null, 2),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'dx', 'float', true, null, null, 3),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'dy', 'float', true, null, null, 4),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'espesor', 'float', true, null, null, 5),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'ancho', 'float', true, null, null, 6),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'velocidad', 'integer', true, null, null, 7),
((SELECT id FROM methods WHERE name = 'proceso_01'), 'bit_coordinador', 'integer', true, null, null, 8);

INSERT INTO parameters (method_id, name, type, required)
VALUES
((SELECT id FROM methods WHERE name = 'modify_output_y'), 'output_id', 'integer', true),
((SELECT id FROM methods WHERE name = 'modify_output_y'), 'value', 'boolean', false);



-- Ordenamiento de parametros por param_order

WITH ordered_params AS (
  SELECT
    id,
    ROW_NUMBER() OVER (PARTITION BY method_id ORDER BY id) AS new_order
  FROM parameters
)
UPDATE parameters t
SET param_order = o.new_order
FROM ordered_params o
WHERE t.id = o.id;

-- Recetas 
CREATE TABLE recetas (
  id SERIAL PRIMARY KEY,
  titulo TEXT NOT NULL DEFAULT 'Receta sin nombre',
  long_caja   NUMERIC(10, 2) NOT NULL CHECK (long_caja > 0),
  ancho_caja  NUMERIC(10, 2) NOT NULL CHECK (ancho_caja > 0),
  altura_caja NUMERIC(10, 2) NOT NULL CHECK (altura_caja > 0),
  long_barra  NUMERIC(10, 2) NOT NULL CHECK (long_barra > 0),
  ancho_barra NUMERIC(10, 2) NOT NULL CHECK (ancho_barra > 0),
  espesor     NUMERIC(10, 2) NOT NULL CHECK (espesor > 0),
  peso        NUMERIC(10, 2) NOT NULL CHECK (peso > 0),
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO recetas (long_caja,ancho_caja,altura_caja,long_barra,ancho_barra,espesor,peso) 
VALUES (3752, 245, 59, 3657, 101, 6.5, 20.80);

-- Alarmas
CREATE TABLE alarmas (
  codigo INTEGER PRIMARY KEY CHECK (codigo > 0),
  mensaje TEXT NOT NULL,
  razon TEXT NOT NULL CHECK (length(razon) > 0),
  solucion TEXT NOT NULL CHECK (length(solucion) > 0)
);

INSERT INTO alarmas (codigo, mensaje, razon, solucion) VALUES
(1, 'Fallo de inicialización', 'Inicialización de datos en progreso', 'Se borrará automáticamente después del arranque'),
(2, 'Configuración de ejes inconsistente entre el host y el controlador manual', 'El controlador manual no coincide con el host', 'Seleccione el host o el controlador manual según se requiera'),
(3, 'Error de parámetros de configuración del eje del host', 'Causa interna', 'Contacte al personal técnico'),
(4, 'Memoria insuficiente', 'El programa de enseñanza es demasiado largo', 'Use módulos para integrar acciones repetitivas. Presione el botón de parada para borrar la alarma.'),
(5, 'Error de análisis de datos de enseñanza', 'Error de programa o incompatibilidad de versión entre el controlador manual y el host', 'Actualice la versión correspondiente del programa. Presione el botón de parada para borrar la alarma.'),
(6, 'Error al editar datos de enseñanza', 'Error al editar el programa', 'Vuelva a cargar o cree un nuevo número de molde. Presione el botón de parada para borrar la alarma.'),
(7, 'Parada de emergencia', '1. El botón de emergencia está presionado. 2. El puerto de emergencia del host no está cableado.', 'Libere el botón de emergencia para borrar la alarma'),
(8, 'Error en autoejecución o salto', 'El salto del programa de enseñanza es inválido o fue eliminado', 'Presione el botón de parada para borrar la alarma'),
(9, 'Fallo de conexión con el host', '1. Error de versión. 2. Error o mala calidad en la línea de comunicación. 3. Bloqueo del host (luz apagada)', '1. Use la versión de programa correspondiente. 2. Revise el cableado de comunicación. 3. Intente reiniciar.'),
(10, 'Error en el programa de enseñanza', 'Mismo que la información de la alarma', 'Revise el programa de enseñanza'),
(11, 'Fallo al guardar los parámetros de configuración', 'Igual que la información de la alarma', 'Restablecer los parámetros o revisar los parámetros de configuración'),
(12, 'Error en la configuración del modelo', 'La cantidad de motores establecida es menor al mínimo del modelo', 'Modifique el modelo o revise la configuración de ejes'),
(15, 'Fallo de comunicación con la placa de E/S', 'Error de comunicación con la placa de E/S', '1. Revise el cableado; 2. Revise la placa principal y la placa de E/S'),
(16, 'Fallo al leer posición absoluta del servo', 'Tiempo de espera excedido en la comunicación', 'Revise el cableado entre host y servo'),
(17, 'Fallo al leer y calibrar posición absoluta del servo', 'Tiempo de espera excedido en la comunicación', 'Revise el cableado entre host y servo'),
(18, 'Error en código de lectura de posición absoluta del servo', 'Tiempo de espera excedido en la comunicación', 'Revise el cableado entre host y servo'),
(19, 'Tiempo de espera al leer posición absoluta del servo', 'Tiempo de espera excedido en la comunicación', 'Revise el cableado entre host y servo'),
(20, 'Fallo de comunicación con la placa de E/S 2', 'Tiempo de espera excedido en la comunicación', '1. Revise el cableado; 2. Revise la placa principal y la placa de E/S'),
(21, 'Fallo de comunicación con la placa de E/S 3', 'Tiempo de espera excedido en la comunicación', '1. Revise el cableado; 2. Revise la placa principal y la placa de E/S'),
(22, 'Fallo de comunicación con la placa de E/S 4', 'Tiempo de espera excedido en la comunicación', '1. Revise el cableado; 2. Revise la placa principal y la placa de E/S'),
(23, 'Fallo de comunicación con la placa de E/S 5', 'Tiempo de espera excedido en la comunicación', '1. Revise el cableado; 2. Revise la placa principal y la placa de E/S'),
(24, 'Alarma FPGA, apague y reinicie', 'Causa interna', 'Contacte al personal técnico'),
(25, 'Error de calibración de salida del módulo de salida analógica', 'Tiempo de espera excedido en la comunicación', 'Revise la línea de comunicación entre el módulo analógico y la placa de control'),
(26, 'Tiempo de espera al leer módulo de salida analógica', 'Tiempo de espera excedido en la comunicación', 'Revise la línea de comunicación entre el módulo analógico y la placa de control'),
(27, 'Error de coordenadas en la mesa de trabajo actual y fallo al cambiar', 'Error en los datos de la mesa de trabajo', 'Revise los datos configurados de la mesa de trabajo'),
(28, 'Error interno', 'Fallo en la solicitud de memoria', 'Optimice el número de molde y reduzca la cantidad de comandos'),
(29, 'La posición se está estabilizando', 'Esperando estabilización de la posición del servo', 'Espere un momento. Contacte al técnico si la falla persiste'),
(30, 'El sistema de coordenadas de la mesa de trabajo no existe', 'Se están usando datos incorrectos de la mesa de trabajo', 'Revise la configuración de la mesa de trabajo'),
(31, 'Mesa giratoria actual no definida', 'Error interno', 'Contacte al personal técnico'),
(32, 'Error de coordenadas en la herramienta actual y fallo al cambiar', 'Se han cambiado datos incorrectos de herramienta', 'Revise los datos de la herramienta'),
(33, 'El sistema de coordenadas de la herramienta actual no existe', 'Se están utilizando datos incorrectos de herramienta', 'Revise los datos de la herramienta'),
(34, 'Fallo de comunicación con la placa EUIO 1', 'Tiempo de espera excedido en la comunicación', 'Revise la conexión de comunicación de la placa EUIO'),
(35, 'Fallo de comunicación con la placa EUIO 2', 'Tiempo de espera excedido en la comunicación', 'Revise la conexión de comunicación de la placa EUIO'),
(36, 'Puerta de seguridad abierta', 'No', 'Cierre las puertas de seguridad'),

(90, 'Alarma en el Motor 1', '1. El cable de conexión entre host y servo está dañado; 2. Falla de alarma del servo', 'Falla en el cableado del motor o en el circuito del host'),
(91, 'Alarma en el Motor 2', '1. El cable de conexión entre host y servo está dañado; 2. Falla de alarma del servo', 'Falla en el cableado del motor o en el circuito del host'),
(92, 'Alarma en el Motor 3', '1. El cable de conexión entre host y servo está dañado; 2. Falla de alarma del servo', 'Falla en el cableado del motor o en el circuito del host'),
(93, 'Alarma en el Motor 4', '1. El cable de conexión entre host y servo está dañado; 2. Falla de alarma del servo', 'Falla en el cableado del motor o en el circuito del host'),
(94, 'Alarma en el Motor 5', '1. El cable de conexión entre host y servo está dañado; 2. Falla de alarma del servo', 'Falla en el cableado del motor o en el circuito del host'),
(95, 'Alarma en el Motor 6', '1. El cable de conexión entre host y servo está dañado; 2. Falla de alarma del servo', 'Falla en el cableado del motor o en el circuito del host'),
(96, 'Alarma en el Motor 7', '1. El cable de conexión entre host y servo está dañado; 2. Falla de alarma del servo', 'Falla en el cableado del motor o en el circuito del host'),
(97, 'Alarma en el Motor 8', '1. El cable de conexión entre host y servo está dañado; 2. Falla de alarma del servo', 'Falla en el cableado del motor o en el circuito del host'),

(100, 'Fallo de movimiento en Eje 1', 'Conflicto de movimientos simultáneos en el mismo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(101, 'Fallo de movimiento en Eje 2', 'Conflicto de movimientos simultáneos en el mismo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(102, 'Fallo de movimiento en Eje 3', 'Conflicto de movimientos simultáneos en el mismo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(103, 'Fallo de movimiento en Eje 4', 'Conflicto de movimientos simultáneos en el mismo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(104, 'Fallo de movimiento en Eje 5', 'Conflicto de movimientos simultáneos en el mismo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(105, 'Fallo de movimiento en Eje 6', 'Conflicto de movimientos simultáneos en el mismo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(106, 'Fallo de movimiento en Eje 7', 'Conflicto de movimientos simultáneos en el mismo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(107, 'Fallo de movimiento en Eje 8', 'Conflicto de movimientos simultáneos en el mismo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),

(110, 'Error de velocidad en Eje 1', 'No especificado', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(111, 'Error de velocidad en Eje 2', 'No especificado', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(112, 'Error de velocidad en Eje 3', 'No especificado', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(113, 'Error de velocidad en Eje 4', 'No especificado', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(114, 'Error de velocidad en Eje 5', 'No especificado', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(115, 'Error de velocidad en Eje 6', 'No especificado', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(116, 'Error de velocidad en Eje 7', 'No especificado', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(117, 'Error de velocidad en Eje 8', 'No especificado', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),

(120, 'Movimiento por encima de velocidad permitida en Eje 1', 'Aceleración de trayectoria demasiado alta', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(121, 'Movimiento por encima de velocidad permitida en Eje 2', 'Aceleración de trayectoria demasiado alta', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(122, 'Movimiento por encima de velocidad permitida en Eje 3', 'Aceleración de trayectoria demasiado alta', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(123, 'Movimiento por encima de velocidad permitida en Eje 4', 'Aceleración de trayectoria demasiado alta', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(124, 'Movimiento por encima de velocidad permitida en Eje 5', 'Aceleración de trayectoria demasiado alta', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(125, 'Movimiento por encima de velocidad permitida en Eje 6', 'Aceleración de trayectoria demasiado alta', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(126, 'Movimiento por encima de velocidad permitida en Eje 7', 'Aceleración de trayectoria demasiado alta', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(127, 'Movimiento por encima de velocidad permitida en Eje 8', 'Aceleración de trayectoria demasiado alta', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),

(130, 'Límite positivo excedido en Eje 1', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(131, 'Límite positivo excedido en Eje 2', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(132, 'Límite positivo excedido en Eje 3', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(133, 'Límite positivo excedido en Eje 4', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(134, 'Límite positivo excedido en Eje 5', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(135, 'Límite positivo excedido en Eje 6', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(136, 'Límite positivo excedido en Eje 7', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(137, 'Límite positivo excedido en Eje 8', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),

(140, 'Límite negativo excedido en Eje 1', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(141, 'Límite negativo excedido en Eje 2', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(142, 'Límite negativo excedido en Eje 3', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(143, 'Límite negativo excedido en Eje 4', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(144, 'Límite negativo excedido en Eje 5', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(145, 'Límite negativo excedido en Eje 6', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(146, 'Límite negativo excedido en Eje 7', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),
(147, 'Límite negativo excedido en Eje 8', 'Movimiento excede el límite suave de un solo eje', 'Presione el botón de parada para borrar la alarma. Reinicie el sistema'),

(9001, 'Robot desconectado', 'No se ha establecido conexión con el robot', 'Verifique el cableado, la red o que el robot esté encendido y accesible');

