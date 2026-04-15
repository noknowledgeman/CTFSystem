FROM node:20-alpine

WORKDIR /app
COPY app/package*.json /app/
RUN npm install --production

COPY app /app
EXPOSE 8080
CMD ["node", "server.js"]
