#!/usr/bin/env bash
set -Eeuo pipefail

echo "🚀 Iniciando servicio con MODE=${MODE:-gateway_robot}"

case "${MODE:-gateway_robot}" in
  command_listener) exec python -u command_listener.py ;;
  gateway_robot)    exec python -u gateway_robot.py ;;
  coordinator)      exec python -u process_coordinator.py ;;
  status)           exec python -u status_listener.py ;;
  *) echo "❌ MODO inválido: ${MODE:-}"; exit 1 ;;
esac