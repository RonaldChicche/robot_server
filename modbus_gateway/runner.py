import os, json, time, signal, sys, logging, redis
from ModbusClient import ModbusGateway

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("runner")

REDIS_HOST = os.getenv("REDIS_HOST","190.168.10.107")
REDIS_PORT = int(os.getenv("REDIS_PORT","6379"))
REDIS_KEY_STATUS  = os.getenv("REDIS_KEY_STATUS","robot:01:sensor_data")
REDIS_KEY_PROCESS = os.getenv("REDIS_KEY_PROCESS","process:state")

gw = None
rd = None
running = True

def shutdown(*_):
    global running, gw
    running = False
    if gw:
        try: gw.disconnect()
        except: pass
    log.info("bye")
    try: sys.exit(0)
    except SystemExit: pass

def i16(x):
    v = int(x)
    return max(-32768, min(32767, v))

def parse_status(payload: dict) -> dict:
    """Mapea el JSON de estado → claves del YAML 'write.robot1'."""
    st = {}
    s   = payload.get("status", {})
    sin = s.get("status", {})

    st["running"] = bool(payload.get("movement_status"))

    y = s.get("outputs", {}).get("y", {})
    st["terminado"]     = 1 if y.get("y33") else 0
    st["set_ok"]        = 1 if y.get("y45") else 0
    st["stack_ready"]   = 1 if y.get("y35") else 0
    st["layer_ready"]   = 1 if y.get("y36") else 0
    st["gripper_state"] = 1 if y.get("y23") else 0

    st["alarm_code"] = int((sin.get("alarm_code") or [0])[0])

    cnt = s.get("counters", {})
    st["stack_count"] = int(cnt.get("counter-2", {}).get("current", 0))

    wp = sin.get("world_position", [0,0,0,0,0,0])
    st.update({
        "pos_x": i16(wp[0]), "pos_y": i16(wp[1]), "pos_z": i16(wp[2]),
        "ang_u": i16(wp[3]), "ang_v": i16(wp[4]), "ang_w": i16(wp[5]),
    })

    tq = sin.get("axis_torque", [0,0,0,0,0,0])
    st.update({f"j{i+1}": i16(tq[i]) for i in range(6)})

    # normaliza booleans a 0/1 (uint16)
    for k, v in list(st.items()):
        if isinstance(v, bool):
            st[k] = 1 if v else 0
    return st

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    try: signal.signal(signal.SIGTERM, shutdown)
    except Exception: pass  # Windows

    gw = ModbusGateway(config_path="config.yaml", kafka_producer=None)
    rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    robot_key = "robot1"

    log.info("loop...")
    while running:
        try:
            # 1) Estados desde Redis → Modbus (solo difs, con confirmación)
            raw = rd.get(REDIS_KEY_STATUS)
            if raw:
                data = json.loads(raw)
                if data.get("robot_id") in ("01", "1"):
                    st = parse_status(data)
                    gw.write_status_diff(robot_key, st, confirm=True)

            # 2) process:state → luces (si no hay valor, apaga todo)
            ps = rd.get(REDIS_KEY_PROCESS) or ""
            lights = {
                "state_green":  1 if ps == "Running" else 0,
                "state_yellow": 1 if ps == "Paused"  else 0,
                "state_red":    1 if ps == "Stopped" else 0,
            }
            gw.write_status_diff(robot_key, lights, confirm=False)

            # 3) Eventos (READ/coils) → Kafka (si configuraste producer en ModbusGateway)
            gw.poll_events_once()

            time.sleep(0.2)
        except Exception as e:
            log.exception(f"loop error: {e}")
            time.sleep(0.5)

    shutdown()
