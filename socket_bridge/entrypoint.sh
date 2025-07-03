#!/bin/bash
if [ "$MODE" = "kafka_to_modbus" ]; then
    python kafka_to_modbus.py
elif [ "$MODE" = "modbus_to_kafka" ]; then
    python modbus_to_kafka.py
else
    echo "⚠️ Variable MODE no reconocida: $MODE"
    exit 1
fi