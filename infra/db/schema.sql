--
-- Initial database schema for the AI dropshipping platform
--

-- Users of the system (human supervisors, administrators)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI agents registered in the system
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    permissions JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Suppliers of products (dropshipping providers)
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    shipping_time_avg INTEGER,
    reliability_score NUMERIC,
    notes TEXT
);

-- Products available or under test in the catalogue
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id),
    source_url TEXT,
    title TEXT NOT NULL,
    cost_price NUMERIC NOT NULL,
    sale_price NUMERIC NOT NULL,
    score NUMERIC,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Marketing campaigns run on advertising platforms
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    platform TEXT NOT NULL,
    product_id INTEGER REFERENCES products(id),
    spend NUMERIC DEFAULT 0,
    revenue NUMERIC DEFAULT 0,
    roas NUMERIC,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Customer orders
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    shopify_order_id TEXT UNIQUE,
    product_id INTEGER REFERENCES products(id),
    customer_email TEXT,
    payment_status TEXT,
    fulfillment_status TEXT,
    tracking_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Support tickets submitted by customers
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    customer_email TEXT,
    category TEXT,
    priority TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    assigned_agent INTEGER REFERENCES agents(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks assigned to agents
CREATE TABLE IF NOT EXISTS agent_tasks (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    task_type TEXT NOT NULL,
    input_payload JSONB,
    output_payload JSONB,
    status TEXT NOT NULL DEFAULT 'pending',
    requires_approval BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Approvals required for sensitive tasks
CREATE TABLE IF NOT EXISTS approvals (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES agent_tasks(id) ON DELETE CASCADE,
    requested_by_agent INTEGER REFERENCES agents(id),
    approved_by_user INTEGER REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Results of product test campaigns
CREATE TABLE IF NOT EXISTS product_test_results (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    impressions INTEGER,
    clicks INTEGER,
    ctr NUMERIC,
    cpa NUMERIC,
    conversion_rate NUMERIC,
    roas NUMERIC,
    result_label TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit logs recording actions by agents and services
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    actor_type TEXT,
    actor_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- -------------------------------------------------------------------------
-- Product candidates used by the Product Hunter AI
--
-- This table holds product ideas proposed by the AI or manually entered by
-- humans.  Candidates are scored and reviewed before they become actual
-- products.  See the FastAPI application for the endpoint definitions.
--
-- Fields:
--   title: human‑readable name of the product
--   source: optional identifier of where the product idea came from (e.g. TikTok, AliExpress)
--   supplier_url: optional URL to the supplier or listing
--   category: optional category label
--   cost_price: purchase cost of the product (EUR)
--   suggested_sale_price: sale price suggested by the scoring function (EUR)
--   score: overall rating (0–100)
--   status: workflow status: new, reviewed, approved or rejected
--   notes: free‑form notes or rationale
--   created_at: timestamp when the candidate was created

CREATE TABLE IF NOT EXISTS product_candidates (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT,
    supplier_url TEXT,
    category TEXT,
    cost_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    suggested_sale_price NUMERIC(10,2),
    score INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'new',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes to accelerate common queries on status and creation time
CREATE INDEX IF NOT EXISTS idx_product_candidates_status
    ON product_candidates(status);
CREATE INDEX IF NOT EXISTS idx_product_candidates_created_at
    ON product_candidates(created_at DESC);