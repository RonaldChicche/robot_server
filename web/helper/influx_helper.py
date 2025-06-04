from services.config import Config
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS, SYNCHRONOUS

class InfluxHelper:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InfluxHelper, cls).__new__(cls)
            cls._instance.client = InfluxDBClient(
                url=Config.INFLUX_URL,
                token=Config.INFLUX_TOKEN,
                org=Config.INFLUX_ORG
            )
            cls._instance.write_api = cls._instance.client.write_api()
            cls._instance.query_api = cls._instance.client.query_api()
            cls._instance.bucket = Config.INFLUX_BUCKET
            cls._instance.org = Config.INFLUX_ORG
        return cls._instance

    def write_variable(self, nombre, valor, tags=None):
        point = Point("robot_data").tag("variable", nombre).field("valor", valor)
        if tags:
            for k, v in tags.items():
                point.tag(k, v)
        self.write_api.write(bucket=self.bucket, record=point)
        self.write_api.close()

    def write_evento_critico(self, evento, mensaje, tags=None):
        """Síncrono: eventos únicos como fallas o cambios de estado"""
        sync_api = self.client.write_api(write_options=SYNCHRONOUS)

        point = Point("eventos").tag("tipo", evento).field("mensaje", mensaje)
        if tags:
            for k, v in tags.items():
                point.tag(k, v)
        sync_api.write(bucket=self.bucket, record=point)
        sync_api.close()

    def write_log_debug(self, mensaje, tags=None):
        """Asíncrono: trazabilidad o logs internos"""
        async_api = self.client.write_api(write_options=ASYNCHRONOUS)

        point = Point("logs").field("mensaje", mensaje)
        if tags:
            for k, v in tags.items():
                point.tag(k, v)
        async_api.write(bucket=self.bucket, record=point)

    def query_variable(self, nombre, tags=None, start="-1h", limit=10, measurement="robot_data"):
        """
        Consulta valores recientes de una variable.
        :param nombre: nombre de la variable (va como tag 'variable')
        :param tags: diccionario de tags adicionales para filtrar
        :param start: rango de tiempo en Flux (ej: "-1h", "-7d", "2024-01-01T00:00:00Z")
        :param limit: cantidad máxima de resultados
        """
        filters = [
            f'r["_measurement"] == "{measurement}"',
            f'r["variable"] == "{nombre}"'
        ]
        if tags:
            for k, v in tags.items():
                filters.append(f'r["{k}"] == "{v}"')

        filters_string = " and ".join(filters)

        query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: {start})
        |> filter(fn: (r) => {filters_string})
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: {limit})
        '''

        return self.query_api.query(org=self.org, query=query)


influx_helper = InfluxHelper()


'''
Tipo de dato	                        Recomendación
--------------------------------------------------------------------------------
Variables de sensores y ejes	        🟢 Batching
Alarmas, eventos únicos	                🔵 Síncrono
Logs de usuario, trazabilidad debug	    🟠 Asíncrono
Estado de celdas o procesos	            🟢 Batching o 🔵 Síncrono si es puntual

-> Division
Organización (Organization)
 └── Bucket (como una base de datos con retención)
      └── Measurement (como una tabla)
           └── Field (dato medido)
           └── Tag (metadato indexado)
           └── Time (timestamp obligatorio)

-> Ejemplo de Estructura en uso
point = (
    Point("temperatura")
    .tag("robot", "UR5")
    .tag("linea", "A1")
    .field("valor", 36.5)
    .time(datetime.utcnow())
)
'''