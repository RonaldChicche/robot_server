FROM python:3.10-slim

WORKDIR /app

#COPY . .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puedes exponer si alguno usa HTTP o healthcheck
#EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
