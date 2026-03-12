This ultimate summary outlines multi-tenant e-commerce ecosystem. It is designed for high horizontal scalability, data sovereignty for partners, and a frictionless experience for customers.

---

## **I. Core Architecture Philosophy**

The platform operates on a **Database-per-Service** and **Database-per-Tenant** model. This ensures that a traffic spike on one reseller's store doesn't affect the stability of the supply chain or other retailers.

* **Communication:** Asynchronous via **Kafka** (Event-Driven).  
* **Routing:** Dynamic Reverse Proxy (Nginx/OpenResty) using **Redis** for domain-to-tenant mapping.  
* **Consistency:** Managed via the **Saga Pattern** (Distributed Transactions).

---

## **II. Microservice Map**

| Service | Primary Responsibility | Data Isolation |
| :---- | :---- | :---- |
| **Identity** | Auth (SSO), RBAC, and Partner Discovery (Connections). | Global MySQL |
| **Brand** | Federation layer that provides unified API access to Brand catalogs across Per-Tenant databases. Manages version control, permission-based access control, and catalog query routing. Each Brand organization gets dedicated tenant database. | **Per-Tenant MySQL** |
| **Supplier** | Supplier operations including product pricing, Brand catalog imports (with pricing), production inventory, and fulfillment management. Each Supplier gets dedicated tenant database. | **Per-Tenant MySQL** |
| **Supply Chain** | Order Orchestration, Fulfillment Rules, and Contract Enforcement. | Operational MySQL |
| **Payment** | Transaction Clearing, Split Payments (Stripe Connect), and Ledgers. | Financial MySQL |
| **Retailer** | Customer Storefronts and Local Catalog Overrides. | **Per-Tenant MySQL** |
| **Platform Ops** | Billing, Global Analytics, and System Administration. | Management MySQL |
| **Notification** | Transactional Alerts (Email, SMS, Slack). | Utility MySQL |

---

## **II.A. Account Type Definitions**

The platform supports three **mutually exclusive** account types. Each organization must choose exactly one type—vertically integrated companies operating across multiple tiers must create separate organizations (e.g., "Newblinds Brand", "Newblinds Supplier", "Newblinds Retail").

### **Brand Account**
**Examples:** Louvolite, Coulisse, Top Window Covering, Decora

**Database:** Dedicated Per-Tenant MySQL (e.g., `blindstrader_brand_louvolite`)

**Primary Responsibilities:**
* Design and manufacture fabrics, components, and blind system parts
* Create verified master catalogs with rich content (technical specs, fabric scans, lifestyle images, PDFs, videos)
* Grant granular permissions to Suppliers for catalog access
* Track content distribution and performance analytics across the supply chain
* Manage product lifecycle (updates, discontinuations) with downstream propagation

**Key Challenge Solved:** Ensures brand integrity by preventing "bastardization" where Suppliers substitute cheaper components or misrepresent products, while enabling controlled distribution of high-quality content to reach end customers.

### **Supplier Account**
**Examples:** Cassidy, Stewarton, Blindlux

**Database:** Dedicated Per-Tenant MySQL (e.g., `blindstrader_supplier_cassidy`)

**Primary Responsibilities:**
* Fabricate made-to-measure blind products using Brand components or custom designs
* **Import Brand-verified catalogs:** Copy fabrics/blind types from connected Brands into Supplier tenant database with "blue tick" verification
* **Create custom products:** Build products not tied to any Brand (e.g., proprietary designs, generic components)
* **Store Supplier-specific pricing** for both Brand-imported and custom products
* Manage production inventory and fulfill orders for connected Retailers
* Publish finished product catalogs (mix of Brand-verified and custom) to Retailers

**Catalog Composition:** Supplier catalogs contain:
1. **Brand-verified products:** Imported from Brand catalogs, retain verification badges
2. **Custom/unbranded products:** Created by Supplier, no Brand verification
3. **Hybrid products:** Use some Brand components + custom elements (partial verification)

**Value Proposition:** Access to verified Brand content and components with transparent sourcing, plus flexibility to offer proprietary products, enabling comprehensive catalog for downstream partners.

### **Retailer Account**
**Examples:** Newblinds, Retailer 2

**Database:** Dedicated Per-Tenant MySQL (e.g., `blindstrader_retailer_newblinds`)

**Primary Responsibilities:**
* Operate customer-facing storefronts (each with dedicated Per-Tenant MySQL database)
* Connect with and adopt Supplier product catalogs (cannot create own products)
* **Pure reseller model:** Retailers sell Supplier products and cannot add their own manufactured products
* Set retail pricing for adopted products and manage local inventory visibility
* Process customer orders and monitor fulfillment status (fulfilled by Suppliers)
* Benefit from Brand-verified content flowing through connected Suppliers

**Catalog Constraints:** Retailers can only:
* Adopt products from connected Suppliers
* Set retail pricing and descriptions
* Choose which Supplier products to display
* **Cannot** create, manufacture, or add products not sourced from a Supplier

**Customer Experience:** End customers see "blue tick" indicators on products made with verified Brand components, building trust and transparency.

---

## **II.B. Connection & Discovery Model**

The platform uses a **mutual bidirectional discovery system** where any tier can initiate connections with adjacent tiers:

### **Brand ↔ Supplier Connections**
* **Suppliers** can browse Brand catalogs and request connections
* **Brands** can discover Suppliers and send connection invitations
* **Both directions require acceptance** by the target organization
* Upon approval, the Identity Service updates the connection status and the Supply Chain Service:
  * Creates trading rules and operational contracts
  * Grants granular catalog access permissions (e.g., specific fabric collections or blind type categories)
  * Enables Kafka event subscriptions for catalog updates

### **Supplier ↔ Retailer Connections**
* **Retailers** can discover Suppliers and request product catalog access
* **Suppliers** can invite Retailers to adopt their product lines
* **Both directions require acceptance**
* Upon approval:
  * Product data is synchronized to the Retailer's Per-Tenant database
  * Retailer gains access to Supplier inventory and fulfillment APIs
  * Pricing and content updates propagate via Kafka events

### **Connection Lifecycle**
* **Pending:** Connection requested, awaiting target approval
* **Approved:** Active trading relationship with full catalog access
* **Rejected:** Connection declined (requester can re-request after 30 days)
* **Suspended:** Temporarily paused by either party (reversible)
* **Terminated:** Permanently ended (catalog access revoked, historical data retained)

---

## **III. The 3-Tier Supply Chain Flow**

The platform's unique value lies in how it connects component manufacturers (Brands) through fabricators (Suppliers) to retail storefronts (Retailers), with verified content and quality assurance flowing through each tier:

### **Step 1: Brand-Supplier Connection**
* **Either party initiates:** Supplier discovers Louvolite's fabric catalog and requests access, OR Louvolite invites Cassidy to use their components
* **Approval workflow:** Target organization reviews and accepts/rejects connection
* **Outcome:** Supply Chain Service creates trading rules and grants Cassidy permission to import Louvolite's verified catalog

### **Step 2: Catalog Import with Verification**
* **Supplier imports Brand catalog:** Cassidy imports Louvolite fabrics and "Allure Roller Blind" type into their **Supplier tenant database** (`blindstrader_supplier_cassidy`)
* **Supplier adds pricing:** For each imported fabric/component, Cassidy stores their wholesale pricing (Brand pricing + markup)
* **"Blue Tick" verification:** Imported items retain `brand_id` and `brand_verified` flags referencing source Brand
* **Version tracking:** Catalog items reference specific Brand catalog versions (e.g., Louvolite Fabrics v2.3)

### **Step 3: Product Fabrication**
* **Supplier builds products:** Cassidy creates products in their tenant database
* **Three product types:**
  * **Fully Brand-verified:** Uses only Louvolite components (e.g., "Premium Roller Blind with Louvolite Fabric") → inherits "blue tick" verification
  * **Custom/unbranded:** Cassidy's proprietary designs using generic components (e.g., "Cassidy House Brand Roller") → no Brand verification, but still Supplier-guaranteed quality
  * **Hybrid/partial verification:** Uses some Brand components + custom elements → flagged as "partially verified" with transparency on which components are Brand-verified
* **Publish to Kafka:** Complete product catalog (all three types) published via `SupplierProductPublished` event

### **Step 4: Retailer-Supplier Connection**
* **Either party initiates:** Newblinds discovers Cassidy's product line and requests connection, OR Cassidy invites Newblinds
* **Approval workflow:** Target accepts/rejects connection
* **Outcome:** Product data synchronized to Newblinds' Per-Tenant database

### **Step 5: Retail Adoption & Pricing**
* **Catalog sync:** Cassidy's complete product catalog (Brand-verified + custom products) cloned to Newblinds' tenant database
* **Retailer capabilities:** 
  * Set retail pricing for each product
  * Add custom marketing descriptions and local SEO content
  * Choose which products to display on storefront
  * **Cannot modify product specifications** (Brand-verified technical specs are immutable)
  * **Cannot add own manufactured products** (pure reseller model)
* **Content inheritance:** 
  * Brand-verified products display Louvolite's rich content (images, videos, PDFs) with attribution
  * Custom Supplier products display Cassidy's provided content
  * Verification badges flow through to Retailer storefront

### **Step 6: Customer Transaction**
* **Purchase:** End customer buys "Premium Roller Blind" on Newblinds.com, seeing "Verified by Louvolite" badge
* **Payment split:** Payment Service instantly distributes funds:
  * **Louvolite (Brand):** Component cost + royalty
  * **Cassidy (Supplier):** Fabrication cost + margin
  * **Newblinds (Retailer):** Retail margin
  * **Platform:** Transaction fee
* **Order routing:** Supply Chain Service routes order to Cassidy for fulfillment
* **Fulfillment:** Cassidy fabricates and ships, updating order status via API (visible to Newblinds and end customer)

---

## **IV. Data & Inventory Strategy**

### **Per-Tenant Database Architecture**
The platform uses **Per-Tenant MySQL databases** for all three account types to ensure complete data sovereignty:

* **Brand Tenants:** `blindstrader_brand_{name}` (e.g., `blindstrader_brand_louvolite`)
  * Stores: Fabrics, blind types, components, technical specs, rich content metadata
  * Ownership: Brand has full control over their master catalog
  
* **Supplier Tenants:** `blindstrader_supplier_{name}` (e.g., `blindstrader_supplier_cassidy`)
  * Stores: Imported Brand catalog items with Supplier pricing AND custom/unbranded products created by Supplier
  * References: `brand_id` and `brand_item_id` for imported Brand products (maintains verification chain)
  * Custom products: No `brand_id` reference, Supplier owns full product definition
  
* **Retailer Tenants:** `blindstrader_retailer_{name}` (e.g., `blindstrader_retailer_newblinds`)
  * Stores: Adopted Supplier product catalogs with retail pricing, customer data, orders, marketing content
  * References: `supplier_id` and `supplier_product_id` with inherited Brand verification metadata
  * **No product creation:** Retailers cannot add products not sourced from connected Suppliers

### **Cross-Tenant Catalog Access**

**Brand Service (Federation Layer):**
* **Stateless API:** Routes catalog queries to appropriate Brand/Supplier tenant databases
* **Permission enforcement:** Validates connection approvals before allowing cross-tenant queries
* **Query examples:**
  * Supplier queries: `GET /brands/louvolite/fabrics?connected=true` → Routes to `blindstrader_brand_louvolite`
  * Retailer queries: `GET /suppliers/cassidy/products?connected=true` → Routes to `blindstrader_supplier_cassidy`
* **Response caching:** Redis caches frequently accessed catalog data with permission tags

**Data Synchronization:**
* **Import flow:** When Cassidy imports Louvolite fabric:
  1. Brand Service queries `blindstrader_brand_louvolite` for fabric data
  2. Data copied to `blindstrader_supplier_cassidy` with `brand_id=louvolite`, `brand_verified=true`
  3. Cassidy adds `supplier_price` column with their wholesale pricing
  4. Kafka event `SupplierCatalogImported` published for audit trail

* **Update propagation:** When Louvolite updates fabric specs:
  1. Brand updates `blindstrader_brand_louvolite` database
  2. Kafka event `BrandCatalogUpdated` published with version bump (v2.3 → v2.4)
  3. Connected Suppliers receive notification
  4. Suppliers opt-in to update via API call, triggering re-sync to their tenant database

### **Brand Catalog Verification**
* **Verification flag propagation:**
  ```sql
  -- Brand owns the source of truth
  brand_fabrics.brand_verified = TRUE (always for Brand-created content)
  
  -- Supplier references with verification inheritance
  supplier_products.brand_fabric_id → brand_fabrics.id
  supplier_products.is_brand_verified = COMPUTED (checks all component FKs)
  
  -- Retailer syncs with verification metadata
  retailer_products.brand_verification_status = ENUM('fully', 'partial', 'none')
  ```
* **Version control:** Each Brand catalog update increments version (e.g., `v2.3` → `v2.4`), stored in Brand tenant database
* **Opt-in propagation:** Suppliers explicitly adopt new versions via Brand Service API, triggering data sync to Supplier tenant database and Kafka `CatalogVersionAdopted` event
* **Redis caching:** Catalog permission lookups cached (`supplier:{id}:brand_access:{brand_id}` → permissions JSON) with 1-hour TTL

### **Inventory Tracking**
* **Brand level:** Raw materials and component inventory tracked in Brand tenant databases (fabrics by meter, motors by unit count)
* **Supplier level:** Finished product inventory and production materials tracked in Supplier tenant databases (made-to-measure items, lead times)
* **Atomic locks:** Shared Redis cluster prevents overselling across tenant databases:
  ```
  REDIS KEY: inventory:brand:louvolite:fabric:1234
  VALUE: {available: 5000, reserved: 150, unit: "meters"}
  
  REDIS KEY: inventory:supplier:cassidy:product:9876
  VALUE: {available: 25, reserved: 3, lead_time_days: 7}
  ```
* **Real-time sync:** Inventory changes in tenant databases publish to Kafka, updating Redis caches within 2 seconds

### **Orders & Fulfillment**
* **Orders:** Stored in Retailer's Per-Tenant DB for customer history, but orchestrated by Supply Chain Service for fulfillment routing
* **Component traceability:** Each order records Brand component versions used (e.g., "Louvolite Fabric v2.3, Motor v1.8") for quality assurance and warranty claims

### **Identity & Multi-Tier Access**
* **Centralized SSO:** Single user can access multiple organizations across tiers (e.g., user is admin at "Louvolite" Brand and consultant at "Cassidy" Supplier)
* **Organization-scoped permissions:** User's role and permissions determined by current organization context
* **Session management:** Redis stores session with organization_id, user sees different UI/data based on active organization
* **Audit trail:** All actions logged with both `user_id` and `organization_id` for cross-organization activity tracking

---

## **V. Platform Management & Revenue**

You manage the system through the **Platform Ops Service** (built with Laravel Filament).

### **Monetization**
* **Metered billing:** Tracks usage across account types via Stripe:
  * **Brands:** Per-GB content storage, API calls, number of connected Suppliers
  * **Suppliers:** Transaction fees, catalog sync volume, number of active products
  * **Retailers:** Per-tenant database cost, transaction fees, monthly active customers
* **Tiered pricing:** Bronze/Silver/Gold plans with different feature access (e.g., Gold Brands get advanced analytics)
* **Revenue split:** Platform takes 2-5% of each transaction (configurable per organization tier)

### **Governance & Brand Protection**

**Brand Verification Workflow:**
1. New Brand account registration requires manual approval by Platform Ops team
2. Identity validation: Business registration documents, trademark certificates, supplier contracts
3. Upon approval, Brand receives "Verified Brand" badge visible across platform
4. Rejection appeals handled through dispute resolution system

**Brand Analytics Dashboard:**
Brands access comprehensive performance metrics via Filament panel:
* **Distribution reach:**
  * Number of connected Suppliers actively using Brand catalog
  * Number of Retailers selling products with Brand components
  * Geographic distribution map of downstream partners
* **Content performance:**
  * Views/downloads of fabric scans, videos, PDFs across all storefronts
  * Conversion rates for fully-verified vs. partially-verified products
  * A/B testing results for content variations
* **Component usage:**
  * Most popular fabrics/blind types by sales volume
  * Average pricing across Retailers (anonymized)
  * Substitution rates (% of products deviating from Brand specs)
* **Quality alerts:**
  * Suppliers with high substitution rates flagged for review
  * Products incorrectly claiming Brand verification
  * Customer reviews mentioning quality issues with Brand components

**Privacy protection:** Analytics aggregated to protect Supplier/Retailer competitive data. Individual partner sales figures never shown to Brands—only aggregated trends.

**Dispute Resolution:**
Platform Ops mediates conflicts:
* **Catalog misuse:** Supplier using Brand content without permission → automatic access revocation + warning
* **Misrepresentation:** Retailer falsely claiming "Brand-verified" → product delisting + penalty
* **Unauthorized modifications:** Supplier altering Brand content (e.g., photoshopping logos onto unapproved products) → catalog suspension
* **Discontinuation disputes:** Supplier contests fabric discontinuation during active orders → Platform enforces grace period policy

**Connection Monitoring:**
* Real-time dashboard showing all Brand → Supplier → Retailer connection chains
* Traceability for compliance: "Which Retailers are selling products with Louvolite Fabric #1234?"
* Audit logs for regulatory requirements (e.g., fire safety standard updates requiring product recalls)

**System Health:**
* Kafka lag monitoring (catalog update propagation delays)
* Redis cache hit rates for permission lookups
* Per-tenant database performance metrics
* API rate limiting and abuse detection

---

## **VI. Implementation Stack**

* **Backend:** Laravel 11+ (leveraging stancl/tenancy for the Reseller layer).  
* **Frontend:** Laravel + livewire (Storefronts) and Filament PHP (Admin Panels).  
* **Events:** Kafka (for reliability) and Redis (for speed).  
* **DevOps:** Docker/Kubernetes with individual MySQL containers for tenants.

This architecture provides the "Lego-block" flexibility needed to grow from 10 users to 10,000 without a total rewrite.

---

## **VII. Appendix**

### **A. Brand Service Explained: Federation Layer**

The Brand Service acts as a **stateless orchestration layer** that sits between clients and the actual catalog data stored in Brand/Supplier tenant databases.

**What "Federation" Means:**  
Instead of having one big database with all catalogs, each Brand has their own isolated database (`blindstrader_brand_louvolite`, `blindstrader_brand_coulisse`). The Brand Service **federates** (unifies) access to these separate databases through a single API.

**Key Responsibilities:**

1. **Unified API Access**
   - Suppliers call one endpoint: `GET /api/catalog/fabrics?brand_id=louvolite`
   - Brand Service determines which tenant database to query (`blindstrader_brand_louvolite`)
   - Returns data as if it came from one system, hiding the multi-tenant complexity

2. **Permission-Based Access Control**
   - Checks if requesting Supplier has approved connection with Brand
   - Validates which blind types/fabrics the Supplier is granted access to
   - Uses Redis cache: `catalog:permissions:supplier_123:brand_456` → `["blind_type_A", "fabric_X"]`

3. **Version Control Management**
   - Tracks which catalog version each Supplier has adopted
   - Maps requests: `GET /catalog/blindtype/roller?version=1.2` → correct Brand tenant schema
   - Prevents breaking changes when Brands update catalogs

4. **Query Routing**
   - Determines target database from request context
   - Example: Retailer requests Supplier's products → routes to `blindstrader_supplier_cassidy`
   - Example: Supplier browses Brand catalog → routes to `blindstrader_brand_louvolite`

**What It Does NOT Do:**
- Does not store primary catalog data (no fabrics table in Brand Service database)
- Does not duplicate Brand content (Suppliers import copies into their own tenant DBs)
- Does not own data (Brands own master catalog, Suppliers own their pricing/modifications)

**Example Flow:**
```
1. Cassidy (Supplier) requests: GET /api/catalog/fabrics?brand=louvolite
2. Brand Service checks Redis: "Does Cassidy have permission to Louvolite catalog?"
3. If yes, connects to blindstrader_brand_louvolite database
4. Executes query: SELECT * FROM fabrics WHERE is_published = true
5. Returns unified JSON response to Cassidy
6. Cassidy imports selected fabrics into blindstrader_supplier_cassidy with pricing
```

This architecture allows Brands to maintain full control over their data while providing Suppliers seamless access through a single API, similar to how GraphQL Federation works for microservices.

---

### **B. Single Account Type Architecture Decision**

The platform enforces a **one-account-type-per-organization constraint**. Each organization must be exclusively a Brand, Supplier, OR Retailer. Vertically integrated companies operating across multiple tiers must create separate organizations (e.g., "Newblinds Brand LLC", "Newblinds Manufacturing Inc.", "Newblinds Retail Ltd.").

### **Rationale: Why Not Multi-Type Accounts?**

While multi-type accounts seem convenient for vertically integrated companies, they introduce significant architectural complexity:

#### **A. Database Isolation Conflicts**
All three account types use **Per-Tenant MySQL databases**, but they serve fundamentally different purposes:

* **Brand catalogs:** `blindstrader_brand_{name}` — Master catalog data with version control
* **Supplier operations:** `blindstrader_supplier_{name}` — Imported catalogs with Supplier pricing, production inventory, fulfillment
* **Retailer storefronts:** `blindstrader_retailer_{name}` — Customer-facing catalogs with retail pricing, orders, customer data

Mixing these in a multi-type account creates tenant identity conflicts:
```sql
-- If Newblinds is both Brand AND Supplier:
-- Single tenant: blindstrader_newblinds
--   Problem 1: Which schema? Brand tables + Supplier tables = bloated schema
--   Problem 2: Self-referential imports (Newblinds-Supplier imports from Newblinds-Brand)
--   Problem 3: How does Brand Service route queries to this hybrid tenant?

-- OR separate tenants: blindstrader_brand_newblinds + blindstrader_supplier_newblinds
--   Problem: Now it's effectively separate organizations anyway, proving the constraint

-- If Newblinds is Brand + Supplier + Retailer:
--   Would need: blindstrader_brand_newblinds + blindstrader_supplier_newblinds + blindstrader_retailer_newblinds
--   Result: Three tenant databases = three organizations (same as current architecture requires)
```

#### **B. Permission System Complexity Explosion**
* **Context-aware switching:** User needs to "act as Brand" vs "act as Supplier" in the same session
* **Permission multiplication:** Instead of 20 Brand permissions + 25 Supplier permissions + 30 Retailer permissions (75 total), you need:
  ```
  (20 Brand × 3 contexts) + (25 Supplier × 3 contexts) + (30 Retailer × 3 contexts) = 225 permission checks
  ```
* **RBAC explosion:** Roles must be scoped to contexts: "Brand Catalog Manager", "Supplier Production Manager", "Retailer Admin" → 3× role definitions
* **UI/UX cognitive overhead:** Users constantly switch "hats", leading to errors (e.g., accidentally editing Brand catalog when intending to update Supplier product)

#### **C. Catalog Ownership Ambiguity**
* **Self-referential connections:** If Newblinds is Brand + Supplier:
  * Does Newblinds-as-Supplier "connect" to Newblinds-as-Brand?
  * How do version upgrades work for self-connections?
  * Circular dependency in foreign keys: `supplier_products.brand_id = own_organization_id`
* **Verification semantics break down:**
  * Can Newblinds-as-Supplier give themselves "blue tick" verification?
  * Who audits internal component substitutions?
  * Trust model collapses when Brand and Supplier are the same entity

#### **D. Analytics Data Contamination**
* **Inflated metrics:** If Newblinds is Brand + Supplier:
  * Brand analytics show "1 Supplier using our catalog" (themselves)
  * Supplier adoption metrics are artificially high
  * Platform cannot provide accurate market insights
* **Privacy violations:** Aggregated analytics designed to protect competitive data become meaningless when Brand sees their own Supplier's sales figures

#### **E. Transaction Flow Ambiguity**
* **Payment splits:** When customer buys from Newblinds-Retailer selling Newblinds-Supplier product using Newblinds-Brand fabric:
  * Does Platform split payment to same bank account 3 times?
  * How are internal transfer fees calculated?
  * Tax implications for "selling to yourself"

#### **F. Compliance & Audit Challenges**
* **Regulatory reporting:** Many jurisdictions require separation between manufacturing (Supplier) and retail operations
* **Audit trails:** Forensic accounting becomes complex when same organization appears multiple times in transaction chain
* **Liability:** Product defects attributable to Brand, Supplier, or Retailer? Legal ambiguity when same entity fills multiple roles

### **Benefits of Separate Organizations**

**Clean separation of concerns:**
* Each organization has single database pattern, single permission model, single UI
* Foreign keys and connections are always between distinct entities
* Audit trails explicitly show value flow between legal entities

**Explicit inter-org connections:**
* Even vertically integrated companies benefit from formal connection workflows
* Internal transactions are transparent and auditable
* Can measure performance of each business unit independently

**Scalability:**
* Can deploy Brand, Supplier, Retailer operations in different regions
* Can sell or spin off business units without database surgery
* Third-party partnerships don't require special-casing internal operations

**User experience:**
* Users have distinct logins for distinct roles (prevents accidental cross-contamination)
* Can grant employees access to only relevant organizations
* Role-based access is simple and understandable

### **Implementation for Vertically Integrated Companies**

Companies operating across multiple tiers should:
1. **Create distinct organizations:** "Acme Brand", "Acme Manufacturing", "Acme Retail"
2. **Establish formal connections:** Acme Manufacturing requests connection to Acme Brand (approved immediately by shared management)
3. **Configure automated approvals:** Set connection policies to auto-approve internal organizations
4. **Unified billing:** Platform Ops can aggregate invoices to single parent company for convenience
5. **Shared user access:** Individual users can be members of multiple organizations with appropriate roles

**Result:** Maintains architectural integrity while providing seamless experience for vertically integrated operations.

