#!/bin/bash
echo "🚀 Iniciando servicio con MODE=$MODE"

case "$MODE" in
  command_listener)
    python -u command_listener.py
    ;;
  gateway_robot)
    python -u gateway_robot.py
    ;;
  coordinator)
    python -u coordinator.py
    ;;
  status)
    python -u status_listener.py
    ;;
  *)
    echo "❌ MODO inválido: $MODE"
    exit 1
    ;;
esac
