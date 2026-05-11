FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_TAILSCALE_HOST=pop-os.taildd322d.ts.net
ARG NEXT_PUBLIC_LAN_HOST=192.168.178.10
ENV NEXT_PUBLIC_TAILSCALE_HOST=${NEXT_PUBLIC_TAILSCALE_HOST}
ENV NEXT_PUBLIC_LAN_HOST=${NEXT_PUBLIC_LAN_HOST}
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3003
ENV HOSTNAME=0.0.0.0
COPY --from=builder /app/.next-build/standalone ./
COPY --from=builder /app/.next-build/static ./.next-build/static
# public/ ist optional — nur kopieren wenn vorhanden
RUN mkdir -p ./public
EXPOSE 3003
CMD ["node", "server.js"]
