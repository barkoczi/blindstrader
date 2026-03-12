# BlindStrader — Application URLs

All URLs use HTTPS via Valet (port 443) proxied to Docker nginx (port 8443).  
Local domain resolves via dnsmasq: `*.blindstrader.test → 127.0.0.1`.

---

## API Services

| Service | URL | Health Check | Notes |
|---|---|---|---|
| **Identity** | https://identity.blindstrader.test | `/api/health` | SSO, RBAC, partner discovery |
| **Brand** | https://brand.blindstrader.test | `/api/health` | Catalog federation, permissions |
| **Supplier** | https://supplier.blindstrader.test | `/api/health` | Pricing, inventory, fulfillment |
| **Supply Chain** | https://sc.blindstrader.test | `/api/health` | Order orchestration |
| **Payment** | https://payment.blindstrader.test | `/api/health` | Stripe Connect, split payments |
| **Retailer** | https://retailer.blindstrader.test | `/api/health` | Customer storefronts |
| **Platform** | https://platform.blindstrader.test | `/api/health` | Billing, admin (Filament) |
| **Notification** | https://notification.blindstrader.test | `/api/health` | Email, SMS, Slack alerts |

### Common API endpoints (all services)

| Endpoint | Auth | Description |
|---|---|---|
| `GET /up` | None | Laravel application health (green dot) |
| `GET /api/health` | None | Service-level health check |
| `GET /api/metrics` | Internal only (local: open) | Prometheus metrics scrape |
| `GET /api/v1/...` | Sanctum token | Authenticated API routes |

---

## Monitoring & Admin

| Tool | URL | Auth | Notes |
|---|---|---|---|
| **Grafana** | https://insights.blindstrader.test | `admin` / `admin` | Dashboards, alerting |
| **Prometheus** | https://prometheus.blindstrader.test | `admin` / `admin` | Metrics, query explorer |
| **phpMyAdmin** | http://pa.blindstrader.test | MySQL credentials | DB management (HTTP only) |
| **API Docs** | https://docs.blindstrader.test | None | Scalar API portal |

---

## Root Domain

| URL | Behaviour |
|---|---|
| https://blindstrader.test | Redirects → `https://identity.blindstrader.test` |

---

## Direct Docker Ports (bypass Valet/nginx)

Useful for debugging or internal service-to-service calls from the host.

| Service | Port | URL |
|---|---|---|
| Identity PHP-FPM | 8001 | `http://localhost:8001` |
| Brand PHP-FPM | 8002 | `http://localhost:8002` |
| Supplier PHP-FPM | 8003 | `http://localhost:8003` |
| Supply Chain PHP-FPM | 8004 | `http://localhost:8004` |
| Payment PHP-FPM | 8005 | `http://localhost:8005` |
| Retailer PHP-FPM | 8006 | `http://localhost:8006` |
| Platform PHP-FPM | 8007 | `http://localhost:8007` |
| Notification PHP-FPM | 8008 | `http://localhost:8008` |
| phpMyAdmin | 8010 | `http://localhost:8010` |
| nginx HTTP | 8080 | `http://localhost:8080` |
| nginx HTTPS | 8443 | `https://localhost:8443` |
| Grafana | 3000 | `http://localhost:3000` |
| Prometheus | 9090 | `http://localhost:9090` |
| Loki | 3100 | `http://localhost:3100` |
| node-exporter | 9100 | `http://localhost:9100/metrics` |
| mysql-exporter | 9104 | `http://localhost:9104/metrics` |
| redis-exporter | 9121 | `http://localhost:9121/metrics` |

---

## Production & Staging Domains

| Environment | Service | URL |
|---|---|---|
| **Production** | Identity | https://identity.blindstrader.com |
| | Brand | https://brand.blindstrader.com |
| | Supplier | https://supplier.blindstrader.com |
| | Supply Chain | https://sc.blindstrader.com |
| | Payment | https://payment.blindstrader.com |
| | Retailer | https://retailer.blindstrader.com |
| | Platform | https://platform.blindstrader.com |
| | Notification | https://notification.blindstrader.com |
| **Staging** | Identity | https://identity.stage.blindstrader.com |
| | Brand | https://brand.stage.blindstrader.com |
| | Supplier | https://supplier.stage.blindstrader.com |
| | Supply Chain | https://sc.stage.blindstrader.com |
| | Payment | https://payment.stage.blindstrader.com |
| | Retailer | https://retailer.stage.blindstrader.com |
| | Platform | https://platform.stage.blindstrader.com |
| | Notification | https://notification.stage.blindstrader.com |

---

## Storefront Tenant Routing (Retailer)

Custom retailer domains are routed dynamically via **Lua + Redis** in nginx.

```
Request: https://newblinds.co.uk/
  → Valet (443)
  → Docker nginx catch-all server block
  → Lua: GET redis key "domain:newblinds.co.uk" → "newblinds"
  → FastCGI → retailer PHP-FPM with HTTP_X_TENANT_ID=newblinds
  → stancl/tenancy initialises blindstrader_retailer_newblinds DB
```

Register a new storefront domain:
```bash
docker exec blindstrader-redis redis-cli SET "domain:mystore.com" "tenant_id"
```
