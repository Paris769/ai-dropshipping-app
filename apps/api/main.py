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

app = FastAPI(title="AI Dropshipping API", version="0.3.0")

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

    # Track publication status of the product.  New products created
    # from approved candidates will be set to "draft" by default.
    status: Optional[str] = None


class CreateProductRequest(BaseModel):
    title: str = Field(..., description="Title or name of the product")
    cost_price: float = Field(..., ge=0, description="Cost from the supplier")
    sale_price: float = Field(..., ge=0, description="Retail price")


class ProductUpdate(BaseModel):
    """Payload for updating an existing product.

    Only mutable fields should be included here.  Currently we allow
    changing the sale price and the publication status (e.g. 'draft',
    'published').  Additional fields can be added in the future as
    business requirements evolve.
    """

    sale_price: Optional[float] = Field(None, ge=0, description="New retail price")
    status: Optional[str] = Field(None, description="Publication status: draft or published")


# ---------------------------------------------------------------------------
# Models for product candidates
#
class ProductCandidateCreate(BaseModel):
    """Payload for creating a new product candidate.

    This structure mirrors the fields in the product_candidates table.  The
    scoring function uses cost_price and category/title to compute a score
    and suggested sale price.  See ``score_candidate`` below for the logic.
    """

    title: str = Field(..., description="Name of the proposed product")
    source: Optional[str] = Field(None, description="Where the product idea came from")
    supplier_url: Optional[str] = Field(None, description="URL of the supplier or listing")
    category: Optional[str] = Field(None, description="Category of the product, e.g. 'Home', 'Fitness'")
    cost_price: float = Field(..., ge=0, description="Purchase cost of the product")
    notes: Optional[str] = Field(None, description="Additional notes or rationale for the idea")


class ProductCandidateUpdate(BaseModel):
    """Payload for updating an existing candidate.

    Only the status and notes can be changed by supervisors.  Other fields
    remain immutable once created.
    """

    status: str = Field(..., description="Workflow status: new, reviewed, approved, rejected")
    notes: Optional[str] = Field(None, description="Reviewer notes or rationale")


class ProductCandidate(BaseModel):
    """Representation of a product candidate stored in the database."""

    id: int
    title: str
    source: Optional[str] = None
    supplier_url: Optional[str] = None
    category: Optional[str] = None
    cost_price: float
    suggested_sale_price: Optional[float] = None
    score: int
    status: str
    notes: Optional[str] = None
    created_at: str


# ---------------------------------------------------------------------------
# Scoring logic for product candidates
#
def score_candidate(cost_price: float, category: Optional[str], title: str) -> tuple[int, float]:
    """Compute a score and suggested sale price for a product candidate.

    The scoring algorithm is intentionally simple.  It awards points for low
    cost_price, desirable categories and keywords in the title.  It also
    computes a suggested sale price by applying a multiplier to the cost_price
    and adding a margin.  The returned score is clamped between 0 and 100.
    """
    score = 50

    # Reward cheaper products
    if cost_price <= 10:
        score += 15
    elif cost_price <= 20:
        score += 8

    # Reward certain categories
    if category:
        cat = category.lower()
        if cat in {"home", "kitchen", "fitness", "beauty", "pets", "gadgets"}:
            score += 10

    # Reward keywords in the title
    title_lower = title.lower()
    for kw in ["portable", "mini", "smart", "usb", "travel", "pet"]:
        if kw in title_lower:
            score += 10
            break

    # Compute a simple suggested sale price: cost_price multiplied by 2.8
    suggested_sale_price = round(cost_price * 2.8, 2)

    # Reward high margin
    if suggested_sale_price - cost_price >= 15:
        score += 15

    # Clamp to 0–100
    score = max(0, min(score, 100))
    return score, suggested_sale_price



# ---------------------------------------------------------------------------
# Database helper functions
#
# Supabase returns query results as lists of dictionaries under the
# ``data`` attribute.  If an error occurs the ``error`` attribute will
# contain details.  These helpers convert the raw data into Pydantic
# models or raise HTTP errors.

def _row_to_product(row: dict) -> Product:
    """Convert a row from the ``products`` table into a Product model.

    The ``products`` table may include additional fields such as ``status``.
    When present, these are passed through to the Product model.  Unknown
    fields are ignored.
    """
    return Product(
        id=row["id"],
        title=row["title"],
        cost_price=float(row["cost_price"]),
        sale_price=float(row["sale_price"]),
        score=float(row["score"]) if row.get("score") is not None else None,
        status=row.get("status"),
    )


# Helper to convert a row from the product_candidates table
def _row_to_candidate(row: dict) -> ProductCandidate:
    """Convert a database row into a ProductCandidate model."""
    return ProductCandidate(
        id=row["id"],
        title=row["title"],
        source=row.get("source"),
        supplier_url=row.get("supplier_url"),
        category=row.get("category"),
        cost_price=float(row["cost_price"]),
        suggested_sale_price=float(row["suggested_sale_price"]) if row.get("suggested_sale_price") is not None else None,
        score=int(row["score"]),
        status=row["status"],
        notes=row.get("notes"),
        created_at=row["created_at"],
    )


@app.get("/products", response_model=List[Product])
async def list_products() -> List[Product]:
    """List all products currently registered in the system."""
    # Query all columns required for the Product model.  If you need
    # additional fields, include them here.
    response = (
        supabase_client.table("products")
        .select("id,title,cost_price,sale_price,score,status")
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
        # New products start as drafts by default unless overridden.
        "status": "draft",
    }
    # Use a local variable name other than `response` to avoid
    # shadowing FastAPI's response type and confusing pydantic.  The
    # Supabase client returns a PostgrestResponse-like object with
    # `.data` and `.status_code` attributes. Some versions may not
    # implement `.error`, so we avoid accessing it directly.
    insert_res = supabase_client.table("products").insert(payload).execute()
    # If the insertion failed, PostgrestResponse returns an empty
    # `data` or sets `status_code` outside the 200 range. Check for
    # missing data rather than relying on a non‑existent `error` attribute.
    if not insert_res or not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to insert product")
    # Insert returns a list of inserted rows. Take the first one.
    row = insert_res.data[0]
    return _row_to_product(row)


# ---------------------------------------------------------------------------
# Product update endpoint
@app.patch("/products/{product_id}", response_model=Product)
async def update_product(product_id: int, req: ProductUpdate) -> Product:
    """Update mutable fields of a product.

    This endpoint allows changing the sale price and publication status.  It
    merges provided values onto the existing row.  Unknown products
    return 404.
    """
    # Build the update payload dynamically, ignoring None values.
    payload: dict = {}
    if req.sale_price is not None:
        payload["sale_price"] = req.sale_price
    if req.status is not None:
        payload["status"] = req.status
    if not payload:
        raise HTTPException(status_code=400, detail="No update fields provided")
    # Execute the update
    update_res = (
        supabase_client.table("products")
        .update(payload)
        .eq("id", product_id)
        .execute()
    )
    if not update_res or not update_res.data:
        raise HTTPException(status_code=404, detail="Product not found")
    row = update_res.data[0]
    return _row_to_product(row)


# ---------------------------------------------------------------------------
# Product candidate endpoints
@app.get("/product-candidates", response_model=List[ProductCandidate])
async def list_product_candidates() -> List[ProductCandidate]:
    """List all product candidates ordered by creation time (newest first)."""
    # Query the product_candidates table. Use a local variable name
    # other than `response` to avoid confusion with FastAPI's response.
    query_res = (
        supabase_client.table("product_candidates")
        .select(
            "id,title,source,supplier_url,category,cost_price,suggested_sale_price,score,status,notes,created_at"
        )
        .order("created_at", desc=True)
        .execute()
    )
    # If the query didn't return a list, raise an HTTP 500. Do not rely
    # on a `.error` property which may not exist on the response.
    if not query_res:
        raise HTTPException(status_code=500, detail="Failed to fetch product candidates")
    rows = query_res.data or []
    return [_row_to_candidate(row) for row in rows]


@app.post(
    "/product-candidates", response_model=ProductCandidate, status_code=status.HTTP_201_CREATED
)
async def create_product_candidate(req: ProductCandidateCreate) -> ProductCandidate:
    """Create a new product candidate and compute its score and suggested price."""
    # Compute score and suggested sale price
    score, suggested_sale_price = score_candidate(
        cost_price=req.cost_price,
        category=req.category,
        title=req.title,
    )
    payload = {
        "title": req.title,
        "source": req.source,
        "supplier_url": req.supplier_url,
        "category": req.category,
        "cost_price": req.cost_price,
        "suggested_sale_price": suggested_sale_price,
        "score": score,
        "status": "new",
        "notes": req.notes,
    }
    insert_res = supabase_client.table("product_candidates").insert(payload).execute()
    if not insert_res or not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to insert product candidate")
    row = insert_res.data[0]
    return _row_to_candidate(row)


@app.patch("/product-candidates/{candidate_id}", response_model=ProductCandidate)
async def update_product_candidate(candidate_id: int, req: ProductCandidateUpdate) -> ProductCandidate:
    """Update the status and/or notes of a product candidate.

    When a candidate is approved, a draft product is automatically
    created in the ``products`` table using the suggested sale price
    computed during candidate creation.  The candidate itself remains
    unchanged except for its status and notes.
    """
    payload = {"status": req.status, "notes": req.notes}
    update_res = (
        supabase_client.table("product_candidates")
        .update(payload)
        .eq("id", candidate_id)
        .execute()
    )
    if not update_res:
        raise HTTPException(status_code=500, detail="Failed to update candidate")
    if not update_res.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate_row = update_res.data[0]
    # If the candidate is now approved, create a draft product
    if req.status.lower() == "approved":
        # Fetch the full candidate row to access suggested_sale_price
        query_res = (
            supabase_client.table("product_candidates")
            .select(
                "id,title,cost_price,suggested_sale_price,score"
            )
            .eq("id", candidate_id)
            .single()
            .execute()
        )
        if query_res and query_res.data:
            data = query_res.data
            sale_price = (
                float(data.get("suggested_sale_price"))
                if data.get("suggested_sale_price") is not None
                else float(data["cost_price"]) * 2.8
            )
            product_payload = {
                "title": data["title"],
                "cost_price": float(data["cost_price"]),
                "sale_price": sale_price,
                "score": float(data.get("score")) if data.get("score") is not None else None,
                "status": "draft",
            }
            # Insert the draft product; ignore result if insertion fails
              supabase_client.table
            ("products").insert(product_payload).execute()


# Order models and endpoints
class OrderCreate(BaseModel):
    product_id : int
    quantity: int

class OrderUpdate(BaseModel):
    status: str | None = None
    tracking_code: str | None = None

class Order(BaseModel):
    id: int
    product_id: int
    quantity: int
    status: str
    tracking_code: str | None = None
    created_at: str

def _row_to_order(row: dict) -> Order:
    return Order(
        id=row["id"],
        product_id=row["product_id"],
        quantity=row["quantity"],
        status=row["status"],
        tracking_code=row.get("tracking_code"),
        created_at=row["created_at"],
    )

@app.get("/orders")
def list_orders():
    res = supabase_client.table("orders").select("*").execute()
    return [_row_to_order(item) for item in (res.data or [])]

@app.post("/orders")
def create_order(req: OrderCreate):
    new_row = {
        "product_id": req.product_id,
        "quantity": req.quantity,
        "status": "pending",
    }
    res = supabase_client.table("orders").insert(new_row).execute()
    row = res.data[0]
    return _row_to_order(row)

@app.patch("/orders/{order_id}")
def update_order(order_id: int, req: OrderUpdate):
       
       update_data: dict = {}



    if req.status is not None:
        update_data["status"] = req.status
    if req.tracking_code is not None:
        update_data["tracking_code"] = req.tracking_code
    if update_data:
        supabase_client.table("orders").update(update_data).eq("id", order_id).execute()
    updated = (
        supabase_client.table("orders")
        .select("*")
        .eq("id", order_id)
        .single()
        .execute()
        .data
    )
    return _row_to_order(updated)

 

