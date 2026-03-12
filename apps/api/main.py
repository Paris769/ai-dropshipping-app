"""
FastAPI application for the AI dropshipping backend.

This module exposes a small API surface for the AI dropshipping project.
It provides a health check endpoint and basic CRUD operations for
products. In this revision, the in‑memory product store has been
replaced with real database interactions using Supabase. Environment
variables ``SUPABASE_URL`` and ``SUPABASE_SERVICE_ROLE_KEY`` (or
``SUPABASE_KEY``) must be defined so that the application can
communicate with the Supabase instance. If these variables are not
present, the application will fail to start.

Endpoints:

* ``GET /health`` — returns ``{"status": "ok"}`` if the service is running.
* ``GET /products`` — lists all products from the ``products`` table.
* ``POST /products`` — creates a new product in the ``products`` table.

This implementation relies on the `supabase` Python client. If you
modify the schema, adjust the queries accordingly. For example,
additional fields such as ``supplier_id`` or ``status`` can be passed
through to the Supabase insert call.
"""

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client

# Initialise the Supabase client using environment variables.  This
# requires ``SUPABASE_URL`` and ``SUPABASE_SERVICE_ROLE_KEY`` (or
# ``SUPABASE_KEY``) to be set in the environment.  The service role
# key grants full access to the database and should be used only on
# the server side.
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Supabase configuration missing: please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
    )

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="AI Dropshipping API", version="0.2.0")

# Configure CORS so that the frontend hosted on a different origin (e.g. Vercel)
# can communicate with this API without browser restrictions.  In a production
# deployment you may wish to restrict the allowed origins to only your
# Vercel domain.  For simplicity here we allow all origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str = Field(..., description="Status of the service, 'ok' if healthy")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return a simple status object indicating the service is up."""
    return HealthResponse(status="ok")


class Product(BaseModel):
    id: int
    title: str
    cost_price: float
    sale_price: float
    score: Optional[float] = None


class CreateProductRequest(BaseModel):
    title: str = Field(..., description="Title or name of the product")
    cost_price: float = Field(..., ge=0, description="Cost from the supplier")
    sale_price: float = Field(..., ge=0, description="Retail price")


# ---------------------------------------------------------------------------
# Database helper functions
#
# Supabase returns query results as lists of dictionaries under the
# ``data`` attribute.  If an error occurs the ``error`` attribute will
# contain details.  These helpers convert the raw data into Pydantic
# models or raise HTTP errors.

def _row_to_product(row: dict) -> Product:
    """Convert a row from the ``products`` table into a Product model."""
    return Product(
        id=row["id"],
        title=row["title"],
        cost_price=float(row["cost_price"]),
        sale_price=float(row["sale_price"]),
        score=float(row["score"]) if row.get("score") is not None else None,
    )


@app.get("/products", response_model=List[Product])
async def list_products() -> List[Product]:
    """List all products currently registered in the system."""
    # Query all columns required for the Product model.  If you need
    # additional fields, include them here.
    response = (
        supabase_client.table("products")
        .select("id,title,cost_price,sale_price,score")
        .execute()
    )
    if response.error:
        raise HTTPException(status_code=500, detail=str(response.error))
    rows = response.data or []
    return [_row_to_product(row) for row in rows]


@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(req: CreateProductRequest) -> Product:
    """Create a new product in the database."""
    payload = {
        "title": req.title,
        "cost_price": req.cost_price,
        "sale_price": req.sale_price,
    }
    response = supabase_client.table("products").insert(payload).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=str(response.error))
    # Insert returns a list of inserted rows. Take the first one.
    row = response.data[0]
    return _row_to_product(row)