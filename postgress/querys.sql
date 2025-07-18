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
