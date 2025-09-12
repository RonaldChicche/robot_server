FROM node:22-slim

WORKDIR /app

COPY package*.json ./
ENV NODE_ENV=production
RUN npm ci --omit=dev || npm install --omit=dev

COPY . .

EXPOSE 5000

CMD ["npm", "start"]