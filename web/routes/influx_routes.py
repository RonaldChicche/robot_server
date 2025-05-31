from flask import Blueprint, jsonify
from helper.influx_helper import influx_helper


influx_bp = Blueprint("influx", __name__)

@influx_bp.route("/temperatura", methods=["GET"])
def obtener_temperatura():
    resultados = influx_helper.query_variable("temperatura", limite=5)
    datos = []
    for tabla in resultados:
        for registro in tabla.records:
            datos.append({
                "valor": registro.get_value(),
                "hora": registro.get_time().isoformat()
            })
    return jsonify(datos)
