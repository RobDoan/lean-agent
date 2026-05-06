# v0.2.0 frontend dev service. Mac + Linux only (per design §9).
FROM node:22-slim

WORKDIR /app

# Layer 1: deps.
COPY package.json package-lock.json ./
RUN npm ci

# Layer 2: source (bind-mounted at runtime by docker-compose for hot reload).
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
