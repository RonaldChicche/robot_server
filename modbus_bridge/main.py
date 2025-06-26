import logging, os


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

BRIDGE_MODE = os.getenv("BRIDGE_MODE", "kafka_to_modbus_bridge")
logger = logging.getLogger(BRIDGE_MODE)
logger.info(f"Modbus Bridge mode: {BRIDGE_MODE}")

if __name__ == "__main__": 
    if BRIDGE_MODE == "kafka_to_modbus_bridge":
        from modbus_bridge.kafka_to_modbus import main
        main()
    elif BRIDGE_MODE == "modbus_to_kafka_bridge":
        from modbus_bridge.modbus_to_kafka import main
        main()