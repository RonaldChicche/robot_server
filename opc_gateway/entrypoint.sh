#!/bin/bash

if [ "$MODE" = "kafka_to_opc" ]; then
    python kafka_to_opc.py
elif [ "$MODE" = "opc_to_kafka" ]; then
    python opc_to_kafka.py
else
    echo "⚠️ Variable MODE no reconocida: $MODE"
    exit 1
fi