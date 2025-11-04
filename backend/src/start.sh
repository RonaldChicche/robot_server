#!/bin/bash
FECHA_LIMITE="2025-11-15"
PROY="/home/bertek/robot_server"   

if [[ "$(date +%Y-%m-%d)" > "$FECHA_LIMITE" ]]; then
  cd "$PROY" || exit 1
  echo "Parando contenedores..."
  docker compose down -v --remove-orphans || true
  echo "Desvinculando git y borrando proyecto..."
  rm -rf .git
  cd .. && rm -rf "$PROY"
  echo "Listo."
fi
