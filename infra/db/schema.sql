-- Database schema for AI dropshipping application

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    status VARCHAR(100),
    permissions JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    country VARCHAR(100),
    shipping_time_avg INTEGER,
    reliability_score INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id),
    source_url TEXT,
    title VARCHAR(255),
    cost_price DECIMAL(10,2),
    sale_price DECIMAL(10,2),
    score INTEGER,
    status VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50),
    product_id INTEGER REFERENCES products(id),
    spend DECIMAL(10,2),
    revenue DECIMAL(10,2),
    roas DECIMAL(10,2),
    status VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    shopify_order_id VARCHAR(255),
    product_id INTEGER REFERENCES products(id),
    customer_email VARCHAR(255),
    payment_status VARCHAR(100),
    fulfillment_status VARCHAR(100),
    tracking_code VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    customer_email VARCHAR(255),
    category VARCHAR(100),
    priority VARCHAR(100),
    status VARCHAR(100),
    assigned_agent INTEGER REFERENCES agents(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    task_type VARCHAR(100),
    input_payload JSONB,
    output_payload JSONB,
    status VARCHAR(100),
    requires_approval BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approvals (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES agent_tasks(id),
    requested_by_agent INTEGER REFERENCES agents(id),
    approved_by_user INTEGER REFERENCES users(id),
    status VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_test_results (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    impressions INTEGER,
    clicks INTEGER,
    ctr DECIMAL(5,2),
    cpa DECIMAL(10,2),
    conversion_rate DECIMAL(5,2),
    roas DECIMAL(10,2),
    result_label VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    actor_type VARCHAR(50),
    actor_id INTEGER,
    action VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id INTEGER,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
