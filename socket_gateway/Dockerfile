FROM python:3.10-slim

ENV TINI_VERSION=v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

WORKDIR /app

#COPY . .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puedes exponer si alguno usa HTTP o healthcheck
#EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/tini", "--", "/entrypoint.sh"]
#CMD ["/entrypoint.sh"]
