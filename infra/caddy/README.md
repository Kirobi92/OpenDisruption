# Caddy reverse-proxy

Routes the family PWA at `kirobi.local` and the host's LAN IP to the
internal Docker services. See `Caddyfile` for routing details.

## Quick test

```bash
docker compose up -d caddy web auth api
curl -sf http://localhost/healthz
curl -sf http://localhost/api/auth/health
```

## TLS

The HTTPS site uses Caddy's internal CA (`tls internal`). On first visit
each device will need to trust the certificate once — or run

```bash
docker compose exec caddy caddy trust
```

…on machines where the Caddy binary is installed locally.

## Reload after edits

```bash
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```
