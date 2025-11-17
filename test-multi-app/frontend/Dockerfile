FROM node:20-alpine

WORKDIR /app

RUN addgroup -g 1001 -S nodejs && adduser -S nodeuser -u 1001

COPY package*.json ./
# Use npm ci if package-lock.json exists, otherwise use npm install
RUN if [ -f package-lock.json ]; then npm ci --only=production; else npm install --production; fi && npm cache clean --force

COPY --chown=nodeuser:nodejs . .

USER nodeuser

EXPOSE 5173

CMD ["node", "index.js"]
