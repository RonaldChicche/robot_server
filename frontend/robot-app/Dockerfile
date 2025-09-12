FROM node:22-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci --no-audit --no-fund

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html

RUN printf 'server {\n  listen 80;\n  server_name _;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / { try_files $uri /index.html; }\n  location /assets/ { try_files $uri =404; }\n}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80