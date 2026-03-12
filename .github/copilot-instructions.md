# BlindStrader Project Context

## Tech Stack
- **Framework:** Laravel 11+, Filament 5, PHP 8.3
- **Architecture:** Microservices (monorepo) with Database-per-Service and Database-per-Tenant model
- **Containerization:** Docker Compose / Kubernetes
- **Reverse Proxy:** Nginx/OpenResty with dynamic routing
- **Admin Panels:** Laravel Filament
- **Storefronts:** Laravel + Livewire
- **API:** RESTful with Laravel Sanctum/JWT
- **Event Bus:** Apache Kafka (async event-driven communication)
- **Caching/Routing:** Redis (domain-to-tenant mapping, inventory locks, permissions)
- **Database:** Per-Tenant MySQL (Brand, Supplier, Retailer tenants)
- **Multi-Tenancy:** stancl/tenancy for Retailer layer
- **Monitoring:** Prometheus + Grafana + Loki + Promtail
- **Payments:** Stripe Connect (split payments)
- **Version Control:** Trunk-based (main, release/staging, release/production)
- **Deployment:** Debian Linux EC2
- **Docker Images:** Built with `docker buildx --platform linux/amd64,linux/arm64` for multi-arch support
- **Local Development:** Laravel Valet proxy (*.test domains → 127.0.0.1)

## Core Architecture Philosophy
- **Database-per-Service:** Each microservice has dedicated operational database
- **Database-per-Tenant:** Each Brand/Supplier/Retailer organization gets isolated tenant database
- **Event-Driven:** Asynchronous communication via Kafka
- **Dynamic Routing:** Nginx + Redis for domain-to-tenant mapping
- **Distributed Transactions:** Saga Pattern for cross-service consistency
- **Horizontal Scalability:** Traffic isolation ensures one tenant's spike doesn't affect others

## Microservices Map

| Service | Responsibility | Database | Port |
|---------|---------------|----------|------|
| **Identity** | SSO auth, RBAC, partner discovery, connections | Global MySQL | 8001 |
| **Brand** | Federation layer for Brand catalogs, version control, permission-based access, catalog query routing | Per-Tenant MySQL (`blindstrader_brand_{name}`) | 8002 |
| **Supplier** | Supplier operations, product pricing, Brand catalog imports with pricing, inventory, fulfillment | Per-Tenant MySQL (`blindstrader_supplier_{name}`) | 8003 |
| **Supply Chain** | Order orchestration, fulfillment rules, contract enforcement | Operational MySQL | 8004 |
| **Payment** | Transaction clearing, split payments (Stripe Connect), ledgers | Financial MySQL | 8005 |
| **Retailer** | Customer storefronts, local catalog overrides | Per-Tenant MySQL (`blindstrader_retailer_{name}`) | 8006 |
| **Platform Ops** | Billing, global analytics, system administration (Filament) | Management MySQL | 8007 |
| **Notification** | Transactional alerts (email, SMS, Slack) | Utility MySQL | 8008 |

## Account Type Definitions (Mutually Exclusive)

### 1. Brand Account
- **Examples:** Louvolite, Coulisse, Top Window Covering
- **Database:** `blindstrader_brand_{name}`
- **Role:** Fabric/component manufacturers, master catalog owners
- **Capabilities:**
  - Create verified master catalogs (fabrics, blind types, components)
  - Grant granular permissions to Suppliers for catalog access
  - Track content distribution and analytics
  - Manage product lifecycle with downstream propagation
- **Key Feature:** "Blue tick" verification flows to Suppliers and Retailers

### 2. Supplier Account
- **Examples:** Cassidy, Stewarton, Blindlux
- **Database:** `blindstrader_supplier_{name}`
- **Role:** Made-to-measure blind fabricators
- **Capabilities:**
  - Import Brand-verified catalogs with Supplier-specific pricing
  - Create custom/unbranded products
  - Manage production inventory and fulfillment
  - Publish product catalogs (Brand-verified + custom) to Retailers
- **Catalog Types:** Brand-verified products, custom products, hybrid products

### 3. Retailer Account
- **Examples:** Newblinds
- **Database:** `blindstrader_retailer_{name}`
- **Role:** Customer-facing storefronts (pure resellers)
- **Capabilities:**
  - Connect with and adopt Supplier product catalogs
  - Set retail pricing and manage local inventory visibility
  - Process customer orders (fulfilled by Suppliers)
- **Constraint:** Cannot create/manufacture own products (only adopt from Suppliers)

## 3-Tier Supply Chain Flow
```
Brand → Supplier → Retailer → End Customer
```

1. **Brand-Supplier Connection:** Mutual bidirectional discovery, approval workflow
2. **Catalog Import:** Supplier imports Brand catalog to tenant DB with pricing
3. **Product Fabrication:** Supplier builds products (Brand-verified, custom, or hybrid)
4. **Retailer-Supplier Connection:** Mutual discovery and catalog sync
5. **Retail Adoption:** Retailer sets retail pricing, inherits Brand verification
6. **Customer Transaction:** Payment split across Brand/Supplier/Retailer/Platform

## Key Data Patterns

### Per-Tenant Databases
- **Brand Tenants:** Master catalogs with version control
- **Supplier Tenants:** Imported catalogs + custom products + Supplier pricing
- **Retailer Tenants:** Adopted products + retail pricing + customer orders
- **Federation:** Brand Service routes queries to correct tenant DB based on permissions

### Cross-Tenant Access
- **Brand Service:** Stateless federation layer, permission enforcement, query routing
- **Redis Caching:** Permission lookups (`supplier:{id}:brand_access:{brand_id}`)
- **Kafka Events:** `BrandCatalogUpdated`, `SupplierProductPublished`, `CatalogVersionAdopted`

### Inventory Management
- **Brand Level:** Raw materials in Brand tenant DB
- **Supplier Level:** Finished product inventory in Supplier tenant DB
- **Redis Locks:** Atomic inventory reservations (`inventory:brand:louvolite:fabric:1234`)

### Verification Chain
- `brand_fabrics.brand_verified = TRUE` (Brand tenant DB)
- `supplier_products.is_brand_verified = COMPUTED` (Supplier tenant DB)
- `retailer_products.brand_verification_status = ENUM('fully', 'partial', 'none')` (Retailer tenant DB)

## Directory Structure
```
/services/
  /identity/             #  Identity service (planned)
  /brand/                 # Brand service (planned)
  /supplier/              # Supplier operations 
  /supply-chain/          # Order orchestration (planned)
  /payment/               # Transaction clearing (planned)
  /retailer/              # Storefronts (planned)
  /platform/              # Admin/billing (planned)
  /notification/          # Alerts (planned)
/shared/                  # Shared libraries, DTOs, events
/monitoring/              # Prometheus, Grafana, Loki configs
/nginx/                   # Reverse proxy configs
/ansible/                 # Deployment automation
/terraform/               # Infrastructure as Code
docker-compose.yml
```

## Domains
### Production domains
- identity.blindstrader.com → Identity Service
- brand.blindstrader.com → Brand Service
- supplier.blindstrader.com → Supplier Service
- sc.blindstrader.com → Supply Chain Service
- payment.blindstrader.com → Payment Service
- retailer.blindstrader.com → Retailer Service
- platform.blindstrader.com → Platform Ops Service
- notification.blindstrader.com → Notification Service

### Staging domains
- identity.stage.blindstrader.com → Identity Service
- brand.stage.blindstrader.com → Brand Service
- supplier.stage.blindstrader.com → Supplier Service
- sc.stage.blindstrader.com → Supply Chain Service
- payment.stage.blindstrader.com → Payment Service
- retailer.stage.blindstrader.com → Retailer Service
- platform.stage.blindstrader.com → Platform Ops Service
- notification.stage.blindstrader.com → Notification Service

## Key Conventions
- **API Routes:** `/api/{resource}` (e.g., `/api/brands/louvolite/fabrics`)
- **Admin Routes:** `/admin` (Filament panels)
- **Tenant Isolation:** Connection approval required for cross-tenant queries
- **Event Naming:** `{Service}{Action}` (e.g., `BrandCatalogUpdated`, `SupplierProductPublished`)
- **Version Control:** Catalog versions tracked (e.g., `v2.3`), opt-in propagation
- **Environment Variables:** Per-service `.env` files
- **Laravel Best Practices:** Repository pattern, service classes, form requests, API resources

## Platform Management
- **Billing:** Metered usage via Stripe (storage, API calls, transactions)
- **Governance:** Manual Brand verification, dispute resolution, catalog misuse enforcement
- **Analytics:** Brand distribution reach, content performance, component usage (privacy-protected)
- **Monitoring:** Kafka lag, Redis cache hit rates, per-tenant DB metrics

## Development Workflow
1. Feature branches from `main`
2. PR review and merge to `main`
3. Promote to `release/staging` for QA
4. Deploy to `release/production` after validation
5. Ansible playbooks for automated deployment
6. Terraform for infrastructure provisioning