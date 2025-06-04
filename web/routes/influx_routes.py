from flask import Blueprint, jsonify
from helper.influx_helper import influx_helper


influx_bp = Blueprint("influx", __name__)

@influx_bp.route("/temperatura", methods=["GET"])
def obtener_temperatura():
    """
    Obtiene las últimas 5 mediciones de temperatura
    ---
    responses:
      200:
        description: Datos de temperatura
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  valor:
                    type: number
                  hora:
                    type: string
    """
    resultados = influx_helper.query_variable("temperatura", limite=5)
    datos = []
    for tabla in resultados:
        for registro in tabla.records:
            datos.append({
                "valor": registro.get_value(),
                "hora": registro.get_time().isoformat()
            })
    return jsonify(datos)
