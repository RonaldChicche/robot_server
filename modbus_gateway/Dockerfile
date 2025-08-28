FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini ca-certificates librdkafka1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY runner.py /app/runner.py
COPY ModbusClient.py /app/ModbusClient.py
COPY config.yaml /app/config.yaml

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["python","-u","/app/runner.py"]
