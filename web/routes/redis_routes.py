from flask import Blueprint, jsonify, request
from helper.redis_helper import redis_helper


redis_bp = Blueprint("redis", __name__)

# get value from one key
@redis_bp.route("/redis", methods=["GET"])
def obtener_estado():
    """
    Obtiene el estado guardado en Redis
    ---
    parameters:
      - in: query
        name: key
        schema:
          type: string
        required: false
        description: Clave a consultar (por defecto -> status)
    responses:
      200:
        description: Estado encontrado
        content:
          application/json:
            schema:
              type: object
              properties:
                key:
                  type: string
                status:
                  type: string
      404:
        description: Clave no encontrada en Redis
      500:
        description: Error interno al consultar Redis
    """
    key = request.args.get("key", "status")

    try:
        estado = redis_helper.get(key)
        if estado is None:
            return jsonify({"error": f"No se encontró valor para '{key}'"}), 404
        return jsonify({"key": key, "status": estado}), 200
    except Exception as e:
        return jsonify({
            "error": "Excepción al consultar Redis",
            "detalle": str(e)
        }), 500


# set value to one key
@redis_bp.route("/redis", methods=["POST"])
def setear_estado():
    """
    Setea un estado en Redis
    ---
    parameters:
      - in: query
        name: key
        schema:
          type: string
        required: false
        description: Clave para guardar el estado (por defecto-> status)
      - in: body
        name: status
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - status
              properties:
                status:
                  type: string
    responses:
      200:
        description: Estado almacenado correctamente
        content:
          application/json:
            schema:
              type: object
              properties:
                key:
                  type: string
                status:
                  type: string
      400:
        description: Campo 'status' faltante
      500:
        description: Error al guardar en Redis
    """
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "El campo 'status' es obligatorio"}), 400

    estado = data["status"]
    key = request.args.get("key", "status")
    try:
        response = redis_helper.set_value(key, estado)
        if response == False:
            return jsonify({"error": "Error al guardar en Redis"}), 500
        return jsonify({ "key": key, "status": estado }), 200
    except Exception as e:
        return jsonify({
            "error": "Error al guardar en Redis",
            "detalle": str(e)
        }), 500
