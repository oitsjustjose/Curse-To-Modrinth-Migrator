FROM node:18 AS builder

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run ts:build

FROM node:18-alpine AS server

WORKDIR /usr/src/app
RUN chown -R node:node /usr/src/app

USER node
EXPOSE 5000

COPY package*.json ./
RUN npm install --production

COPY --from=0 /usr/src/app/dist dist

ENV NODE_ENV=production

CMD ["node", "dist/server.js"]
