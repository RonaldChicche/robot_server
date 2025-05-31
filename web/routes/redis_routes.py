from flask import Blueprint, jsonify, request
from helper.redis_helper import redis_helper


redis_bp = Blueprint("redis", __name__)

@redis_bp.route("/estado", methods=["GET"])
def obtener_estado():
    estado = redis_helper.get("estado_robot") or "desconocido"
    return jsonify({"estado": estado})

@redis_bp.route("/estado", methods=["POST"])
def establecer_estado():
    data = request.get_json()
    nuevo_estado = data.get("estado")
    redis_helper.set("estado_robot", nuevo_estado)
    return jsonify({"ok": True, "nuevo_estado": nuevo_estado})
