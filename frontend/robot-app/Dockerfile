FROM node:22-alpine
WORKDIR /app

RUN apk add --no-cache bash libc6-compat libstdc++ curl \
    && apk add --no-cache --virtual .build-deps python3 make g++


EXPOSE 5173