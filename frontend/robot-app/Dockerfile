FROM node:22-alpine

# Tini ya está disponible en Alpine como paquete
RUN apk add --no-cache tini bash libc6-compat libstdc++ curl \
    && apk add --no-cache --virtual .build-deps python3 make g++

WORKDIR /app

# Evita buffering en logs de Node.js
ENV NODE_ENV=development
ENV FORCE_COLOR=1

#EXPOSE 5173

# Usa tini como ENTRYPOINT
ENTRYPOINT ["/sbin/tini", "--"]

# Comando por defecto (puede ser sobrescrito por docker-compose)
CMD ["sh", "-c", "npm install && npm run dev -- --host"]
