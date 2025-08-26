#!/bin/bash
set -Eeuo pipefail

echo "🟢 Entrando a entrypoint.sh con MODE=${MODE:-<no definido>}"

case "${MODE:-}" in
  kafka_to_opc)
    echo "▶️ Ejecutando kafka_to_opc.py"
    exec python -u kafka_to_opc.py
    ;;
  opc_to_kafka)
    echo "▶️ Ejecutando opc_to_kafka.py"
    exec python -u opc_to_kafka.py
    ;;
  *)
    echo "❌ MODE no reconocido: '${MODE:-<no definido>}'"
    exit 1
    ;;
esac