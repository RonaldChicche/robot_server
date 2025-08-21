from common.utils import load_keys, create_redis_client
from JsonBorunteClient import JSONBorunteClient, RobotStateMachine

import os, json, logging, signal, sys, time


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

ROBOT_ID = os.getenv("ROBOT_ID", "01")
BORUNTE_IP = os.getenv("BORUNTE_IP", "localhost")
BORUNTE_PORT = os.getenv("BORUNTE_PORT", "9760")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


logger = logging.getLogger(f"GatewayRobot{ROBOT_ID}")

redis_client = None
robot = None
gateway_keys = {}

def graceful_shutdown(sig=None, frame=None):
    logger.info("🛑 Señal de apagado recibida. Cerrando conexiones...")
    try:
        if redis_client:
            redis_client.close()
            logger.info("✅ Redis cerrado")
    except Exception as e:
        logger.error(f"⚠️ Error cerrando conexiones: {e}", exc_info=True)
    sys.exit(0)

def format_gateway_keys(template: dict, robot_id: str) -> dict:
    """Devuelve un dict con todas las claves Redis formateadas para un robot específico."""
    return {k: v.format(id=robot_id) for k, v in template.items()}

def main():
    global redis_client, robot, gateway_keys
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    logger.info(f"🤖 Gateway de robot:{ROBOT_ID} iniciando ... {BORUNTE_IP}-{BORUNTE_PORT}")
    keys_all = load_keys(path="common/redis_keys.yaml")
    gateway_keys = format_gateway_keys(keys_all["gateway_template"], ROBOT_ID)
    
    try:
        redis = create_redis_client(REDIS_HOST, REDIS_PORT)
        robot = JSONBorunteClient(host=BORUNTE_IP, robot_id=ROBOT_ID, port=BORUNTE_PORT, timeout=5)
        robot.modify_output_y(33, True)
    except Exception as e:
        logger.error(f"❌ Error crítico al inicializar: {e}", exc_info=True)
        graceful_shutdown()

    # Diccionario de métodos permitidos
    method_map = {
        "start_button": robot.start_button,
        "stop_button_single": robot.stop_button,
        "stop_button": robot.action_stop,
        "pause_button": robot.action_pause,
        "clear_alarm_button": robot.clear_alarm,
        "clear_alarm_run_next": robot.clear_alarm_run_next,
        "clear_alarm_and_continue": robot.clear_alarm_and_continue,
        "modify_counter": robot.modify_counter,
        "modify_stack": robot.modify_stack,
        "modify_global_velocity": robot.modify_global_velocity,
        "write_data_single": robot.write_data_single,
        "write_data_block": robot.write_data_block,
        "modify_output_y": robot.modify_output_y,
        "resume_proceso_01": robot.resume_proceso_01,
        "proceso_01": robot.proceso_01,
        "proceso_02": robot.proceso_02,
        "proceso_03": robot.proceso_03,
        "proceso_04": robot.proceso_04,
        "proceso_05": robot.proceso_05,
        "proceso_06": robot.proceso_06
    }

    logger.info("🔄 Iniciando bucle principal...")
    fsm = RobotStateMachine()
    
    last_query_time = 0
    while True:
        command = None
        try:
            cmd_raw = redis.lpop(gateway_keys["cmd_buffer"])
            if cmd_raw:
                command = json.loads(cmd_raw)
                logger.info(f"📥 Recibido para ejecutar: {command}")
                cmd_type = command.get("type")
                cmd_name = command.get("name")
                params = command.get("params", {})

                if cmd_name in method_map:
                    method = method_map[cmd_name]

                    if not isinstance(params, dict):
                        raise ValueError(f"⚠️ Los parámetros deben ser un dict válido: {params}")

                    if cmd_name in ["proceso_01"]:
                        # encender bit y45 ON:
                        robot.modify_output_y(45, True)

                    if cmd_name in ["stop_button", "proceso_02", "proceso_03", "proceso_04", "proceso_05", "proceso_06"]:
                        robot.modify_output_y(30, False)
                        robot.modify_output_y(32, False)
                        #robot.modify_output_y(33, True)
                        robot.modify_output_y(35, False)
                        robot.modify_output_y(36, False)
                        robot.modify_output_y(45, False)
                        
                        robot.write_data_single(855, 0)   

                        # robot.modify_counter("counter-0", 0, 0)
                        # robot.modify_counter("counter-1", 0, 0)
                        # robot.modify_counter("counter-2", 0, 1000)

                    if cmd_name in ["start_button", "pause_button"]:
                        new_state = fsm.handle_command(cmd_name)
                        robot.modify_output_y(45, False)
                        logger.info(f"🔄 Estado FSM → {new_state}")
                        robot.write_data_single(855, 0)  
                        if cmd_name == "start_button":
                            robot.modify_output_y(33, False)
                            time.sleep(1)
                            robot.update_process(1)
                            robot.modify_global_velocity(robot.vel_prod)

                            
                    elif cmd_name in ["stop_button"]:
                        new_state = fsm.handle_command(cmd_name)
                    
                    logger.info(f"🚀 Ejecutando '{cmd_type}' → {cmd_name} con parámetros: {params} {robot.state_ini} -> {robot.state_end} || {robot.x_pick} -> {robot.x_place}")
                    result = method(**params)

                else:
                    logger.warning(f"⛔ Método no permitido: {cmd_name}")
                    result = None

                redis.set(gateway_keys["cmd_result"], json.dumps({
                    "status": "ok",
                    "order_id": command.get("order_id"),
                    "type": cmd_type,
                    "name": cmd_name,
                    "result": result,
                    "timestamp": time.time()
                }))
                #redis.delete(gateway_keys["cmd_buffer"])
                logger.info(f"✅ Comando '{cmd_name}' ejecutado con éxito.")
            
            # Leer estado del robot siempre
            redis.set(gateway_keys["connected"], 1, ex=5)
            if fsm.check_clean():
                logger.info("🧼 Estado reseteado a Vacio tras STOP")
            
            redis.set(keys_all["process_coordinator"]["process_state"], fsm.state)
            # redis.set(gateway_keys["status"], "activo", ex=5)

            if time.time() - last_query_time >= 0.2:
                response = robot.query_all_borunte_data()
                redis.set(gateway_keys["sensor_data"], json.dumps(response))
                new_state = fsm.evaluate_termination(response["status"]["outputs"]["y"])
                logger.info(f"🔄 Estado FSM → {new_state}")
                if response["status"]["status"]["alarm_code"][0] != 0:
                    fsm.handle_command("stop_button")
                    robot.action_stop()
                    robot.modify_output_y(30, False)
                    robot.modify_output_y(32, False)
                    #robot.modify_output_y(33, False)
                    robot.modify_output_y(35, False)
                    robot.modify_output_y(36, False)
                    robot.modify_output_y(45, False)
                last_query_time = time.time()   

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as known_error:
            logger.error(f"⚠️ Error procesando comando inválido: {known_error}", exc_info=True)

        except Exception as fatal_error:
            logger.error(f"💥 Error inesperado. Apagando...{BORUNTE_IP}: {fatal_error}", exc_info=True)
            graceful_shutdown()




if __name__ == "__main__":
    main()