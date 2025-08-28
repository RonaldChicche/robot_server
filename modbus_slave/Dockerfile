FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# COPY modbus_slave.py /app/modbus_slave.py

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5020/tcp
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["python","-u","/app/modbus_slave.py"]
