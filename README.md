# AI Dropshipping Application

This repository contains the initial structure for an AI‑powered dropshipping
platform.  The goal of the platform is to coordinate multiple specialised
agents (product discovery, catalogue management, marketing, fulfilment and
support) while maintaining a clear separation between decision making (AI
agents) and side‑effectful operations (e.g. creating orders, changing
prices).  It includes a web dashboard, a FastAPI backend, service
definitions and placeholder modules for workflow orchestration and
automation.

## Structure

```
ai‑dropshipping‑app/
├── apps/                # Top–level applications
│   ├── web/             # Next.js control panel
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── pages/
│   │       └── index.tsx
│   └── api/             # FastAPI backend
│       ├── requirements.txt
│       └── main.py
├── services/            # Microservices (empty placeholders)
├── workers/             # Long‑running workers (Temporal, etc.)
│   ├── temporal-workers/
│   └── background-jobs/
├── packages/            # Shared packages (types, config, UI components)
├── infra/               # Infrastructure related code
│   ├── docker/          # Dockerfiles and container configs
│   ├── terraform/       # IaC scripts
│   ├── scripts/         # Helper scripts
│   └── db/
│       └── schema.sql   # Initial database schema
├── docs/                # Architecture and design docs
│   └── architecture.md
└── n8n/                 # n8n workflows
    └── workflows/
```

At this stage most folders contain placeholders to provide a skeleton that
will be fleshed out in later iterations.  Only a few concrete files are
included:

* A **FastAPI** backend with a health check endpoint and minimal route
  definitions.
* A **Next.js** front‑end with a simple home page.
* An SQL file defining the initial set of tables for the core domain
  (users, agents, products, suppliers, campaigns, orders, tickets,
  tasks, approvals, product test results and audit logs).

Refer to the `docs/architecture.md` file for an overview of the planned
modules and the high‑level design decisions driving the project.