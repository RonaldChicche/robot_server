FROM node:22-alpine

RUN apk add --no-cache tini bash libc6-compat libstdc++ curl \
    && apk add --no-cache --virtual .build-deps python3 make g++

WORKDIR /app

ENV NODE_ENV=development
ENV FORCE_COLOR=1
ENV CHOKIDAR_USEPOLLING=true

COPY package*.json ./
RUN npm install && apk del .build-deps
COPY . .
#EXPOSE 5173

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["npm", "run", "dev", "--", "--host"]