# Architecture Overview

This document captures the high‑level architecture for the AI dropshipping
platform.  The system is designed to support semi‑autonomous operation
while maintaining safety, traceability and human oversight.  It is
structured around several independent modules, each responsible for a
specific domain.

## Guiding Principles

- **Separation of concerns** – Decision making, side effects and data
  persistence are clearly separated.  AI agents perform analysis and
  propose actions; specialised services perform the actual changes.
- **Event driven** – Significant events (e.g. new order, campaign over
  budget, stock low) trigger workflows that can be automated through
  orchestration layers such as n8n or Temporal.
- **Durable workflows** – Processes involving multiple steps (order
  fulfilment, campaign management) are modelled as durable workflows
  capable of recovering from interruptions.
- **Human‑in‑the‑loop** – Sensitive actions (pricing changes, major
  campaign budget adjustments, refunds, legal communications) require
  explicit approval.  Agents may propose these actions but cannot
  execute them unilaterally.
- **Observability** – All actions by agents and services are logged.
  Monitoring and alerting are integral parts of the system.

## Modules

### Control Panel (apps/web)

A Next.js web application provides a unified dashboard for supervisors.
It shows key metrics (sales, campaign performance, order statuses) and
exposes UI for approving or rejecting sensitive actions proposed by the
agents.  Tailwind CSS is used for styling and shadcn/ui for basic
components.

### Backend (apps/api)

The backend is built with FastAPI.  It exposes REST endpoints for:

* Health checks and configuration.
* CRUD operations on core domain objects (products, suppliers, agents).
* Dispatching tasks to agents and retrieving their results.
* Integrating with the e‑commerce platform via webhooks.

This layer also interacts with the database (via Supabase) and
authenticates requests from the web app or other services.

### Agent Orchestrator

The orchestrator coordinates the various AI agents.  It routes
incoming tasks to the appropriate agent, manages their context and
ensures compliance with approval rules.  Agents are built using
`LangGraph` on top of the OpenAI Responses API to support multi‑turn
tool‑calling.

### Services

Individual services encapsulate responsibilities such as catalogue
management, campaign analysis, fulfilment and customer support.  They
expose functions that the agents can call (e.g. creating a product on
Shopify, pausing a campaign on Meta Ads) and are responsible for
validating input, enforcing limits and writing audit logs.

### Workers

Long‑running or multi‑step processes are implemented as Temporal
workflows.  For example, the order fulfilment pipeline waits for
payment confirmation, sends the order to the supplier and tracks
delivery.  If any step fails, the workflow resumes from where it left
off without data loss.

### Data Layer

Data is stored in a PostgreSQL database managed by Supabase.  The
initial schema is located in `infra/db/schema.sql`.  Key entities
include:

* **Users** – human supervisors and approvers.
* **Agents** – AI agents with their type and permissions.
* **Products** – candidate products to sell and their associated
  metadata (cost, recommended price, scores).
* **Suppliers** – external vendors along with reliability metrics.
* **Campaigns** – marketing campaigns run on Meta or Google ads
  platforms.
* **Orders** – customer orders, payment status and fulfilment state.
* **Tickets** – support requests from customers.
* **Tasks** – tasks dispatched to agents with input/output payloads and
  approval status.
* **Approvals** – approvals required for sensitive actions.
* **Product test results** – data collected from trial campaigns.
* **Audit logs** – record of operations performed by agents or
  services.

### Automation & Integrations

n8n is used for quick integrations (webhooks, simple automations,
notifications) while Temporal orchestrates complex workflows that must
survive restarts or failures.  The OpenAI Responses API provides the
cognitive engine for the agents.  Other integrations include the
Shopify GraphQL Admin API (for e‑commerce operations), Meta Ads,
Google Ads, Stripe and Brevo for communications.

### OpenClaw (Optional)

OpenClaw can be deployed as an interaction layer to receive commands
via messaging channels (WhatsApp, Telegram) and to route them to
agents.  It is not used for critical operations such as order
processing or payments; those are handled by the backend and services.

## Roadmap

The following milestones are suggested for iteratively building the
system:

1. **Setup** – Create repository skeleton, database schema and minimal
   API / web application (complete).
2. **Product Discovery** – Implement Product Hunter agent and its
   integration with the database.
3. **Catalogue Management** – Add catalogue service and agent to
   create/update products on Shopify.
4. **Order Workflow** – Implement reliable order processing using
   Temporal.
5. **Campaign Analysis** – Introduce campaign data ingestion and
   analysis rules.
6. **Customer Support** – Add support agent and ticketing system.
7. **Learning Layer** – Build mechanisms to learn from historical
   performance and refine product/campaign selection.

Subsequent iterations will refine the agents and expand the scope to
cover additional channels and advanced features.
