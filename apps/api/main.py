from __future__ import annotations

from typing import Any
import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client, create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Supabase configuration missing: please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
    )

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="AI Dropshipping API", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")


class Product(BaseModel):
    id: int
    title: str
    cost_price: float
    sale_price: float
    score: float | None = None
    status: str | None = None
    supplier_id: int | None = None


class CreateProductRequest(BaseModel):
    title: str = Field(..., description="Product title")
    cost_price: float = Field(..., ge=0, description="Supplier cost")
    sale_price: float = Field(..., ge=0, description="Retail price")
    supplier_id: int | None = Field(None, description="Optional supplier id")


class ProductUpdate(BaseModel):
    sale_price: float | None = Field(None, ge=0)
    status: str | None = None
    supplier_id: int | None = None


class ProductCandidateCreate(BaseModel):
    title: str
    source: str | None = None
    supplier_url: str | None = None
    category: str | None = None
    cost_price: float = Field(..., ge=0)
    notes: str | None = None


class ProductCandidateUpdate(BaseModel):
    status: str
    notes: str | None = None


class ProductCandidate(BaseModel):
    id: int
    title: str
    source: str | None = None
    supplier_url: str | None = None
    category: str | None = None
    cost_price: float
    suggested_sale_price: float | None = None
    score: int
    status: str
    notes: str | None = None
    created_at: str


class Supplier(BaseModel):
    id: int
    name: str
    contact_info: str | None = None
    shipping_time_days: int | None = None
    reliability_score: float | None = None
    created_at: str | None = None


class SupplierCreate(BaseModel):
    name: str
    contact_info: str | None = None
    shipping_time_days: int | None = Field(None, ge=0)
    reliability_score: float | None = Field(None, ge=0, le=10)


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_info: str | None = None
    shipping_time_days: int | None = Field(None, ge=0)
    reliability_score: float | None = Field(None, ge=0, le=10)


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)


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


def _response_data(response: Any) -> Any:
    return getattr(response, "data", None)


def score_candidate(cost_price: float, category: str | None, title: str) -> tuple[int, float]:
    score = 50

    if cost_price <= 10:
        score += 15
    elif cost_price <= 20:
        score += 8

    if category:
        cat = category.lower()
        if cat in ["home", "kitchen", "fitness", "beauty", "pets", "gadgets"]:
            score += 10

    title_lower = title.lower()
    for keyword in ["portable", "mini", "smart", "usb", "travel", "pet"]:
        if keyword in title_lower:
            score += 10
            break

    suggested_sale_price = round(cost_price * 2.8, 2)

    if suggested_sale_price - cost_price >= 15:
        score += 5

    score = max(0, min(score, 100))
    return score, suggested_sale_price


def _row_to_product(row: dict[str, Any]) -> Product:
    return Product(
        id=row["id"],
        title=row["title"],
        cost_price=float(row["cost_price"]),
        sale_price=float(row["sale_price"]),
        score=float(row["score"]) if row.get("score") is not None else None,
        status=row.get("status"),
        supplier_id=row.get("supplier_id"),
    )


def _row_to_candidate(row: dict[str, Any]) -> ProductCandidate:
    return ProductCandidate(
        id=row["id"],
        title=row["title"],
        source=row.get("source"),
        supplier_url=row.get("supplier_url"),
        category=row.get("category"),
        cost_price=float(row["cost_price"]),
        suggested_sale_price=(
            float(row["suggested_sale_price"])
            if row.get("suggested_sale_price") is not None
            else None
        ),
        score=int(row["score"]),
        status=row["status"],
        notes=row.get("notes"),
        created_at=row["created_at"],
    )


def _row_to_supplier(row: dict[str, Any]) -> Supplier:
    return Supplier(
        id=row["id"],
        name=row["name"],
        contact_info=row.get("contact_info"),
        shipping_time_days=row.get("shipping_time_days"),
        reliability_score=(
            float(row["reliability_score"])
            if row.get("reliability_score") is not None
            else None
        ),
        created_at=row.get("created_at"),
    )


def _row_to_order(row: dict[str, Any]) -> Order:
    return Order(
        id=row["id"],
        product_id=row["product_id"],
        quantity=row["quantity"],
        status=row["status"],
        tracking_code=row.get("tracking_code"),
        created_at=row["created_at"],
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/products", response_model=list[Product])
def list_products() -> list[Product]:
    response = (
        supabase_client.table("products")
        .select("id,title,cost_price,sale_price,score,status,supplier_id")
        .execute()
    )
    rows = _response_data(response)
    if rows is None:
        raise HTTPException(status_code=500, detail="Failed to fetch products")
    return [_row_to_product(row) for row in rows]


@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(req: CreateProductRequest) -> Product:
    payload: dict[str, Any] = {
        "title": req.title,
        "cost_price": req.cost_price,
        "sale_price": req.sale_price,
        "status": "draft",
    }
    if req.supplier_id is not None:
        payload["supplier_id"] = req.supplier_id

    insert_res = supabase_client.table("products").insert(payload).execute()
    rows = _response_data(insert_res)
    if not rows:
        raise HTTPException(status_code=500, detail="Failed to insert product")
    return _row_to_product(rows[0])


@app.patch("/products/{product_id}", response_model=Product)
def update_product(product_id: int, req: ProductUpdate) -> Product:
    payload: dict[str, Any] = {}

    if req.sale_price is not None:
        payload["sale_price"] = req.sale_price
    if req.status is not None:
        payload["status"] = req.status
    if req.supplier_id is not None:
        payload["supplier_id"] = req.supplier_id

    if not payload:
        raise HTTPException(status_code=400, detail="No update fields provided")

    supabase_client.table("products").update(payload).eq("id", product_id).execute()

    fetch_res = (
        supabase_client.table("products")
        .select("id,title,cost_price,sale_price,score,status,supplier_id")
        .eq("id", product_id)
        .single()
        .execute()
    )
    row = _response_data(fetch_res)
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")

    return _row_to_product(row)


@app.get("/product-candidates", response_model=list[ProductCandidate])
def list_product_candidates() -> list[ProductCandidate]:
    query_res = (
        supabase_client.table("product_candidates")
        .select(
            "id,title,source,supplier_url,category,cost_price,suggested_sale_price,score,status,notes,created_at"
        )
        .order("created_at", desc=True)
        .execute()
    )
    rows = _response_data(query_res)
    if rows is None:
        raise HTTPException(status_code=500, detail="Failed to fetch product candidates")
    return [_row_to_candidate(row) for row in rows]


@app.post(
    "/product-candidates",
    response_model=ProductCandidate,
    status_code=status.HTTP_201_CREATED,
)
def create_product_candidate(req: ProductCandidateCreate) -> ProductCandidate:
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
    rows = _response_data(insert_res)
    if not rows:
        raise HTTPException(status_code=500, detail="Failed to insert product candidate")
    return _row_to_candidate(rows[0])


@app.patch("/product-candidates/{candidate_id}", response_model=ProductCandidate)
def update_product_candidate(candidate_id: int, req: ProductCandidateUpdate) -> ProductCandidate:
    before_res = (
        supabase_client.table("product_candidates")
        .select("id,status")
        .eq("id", candidate_id)
        .single()
        .execute()
    )
    before_row = _response_data(before_res)
    if not before_row:
        raise HTTPException(status_code=404, detail="Candidate not found")

    payload = {"status": req.status, "notes": req.notes}
    supabase_client.table("product_candidates").update(payload).eq("id", candidate_id).execute()

    fetch_res = (
        supabase_client.table("product_candidates")
        .select(
            "id,title,source,supplier_url,category,cost_price,suggested_sale_price,score,status,notes,created_at"
        )
        .eq("id", candidate_id)
        .single()
        .execute()
    )
    candidate_row = _response_data(fetch_res)
    if not candidate_row:
        raise HTTPException(status_code=404, detail="Candidate not found after update")

    previous_status = (before_row.get("status") or "").lower()
    new_status = req.status.lower()

    if new_status == "approved" and previous_status != "approved":
        sale_price = (
            float(candidate_row["suggested_sale_price"])
            if candidate_row.get("suggested_sale_price") is not None
            else float(candidate_row["cost_price"]) * 2.8
        )
        product_payload = {
            "title": candidate_row["title"],
            "cost_price": float(candidate_row["cost_price"]),
            "sale_price": sale_price,
            "score": (
                float(candidate_row["score"])
                if candidate_row.get("score") is not None
                else None
            ),
            "status": "draft",
        }
        supabase_client.table("products").insert(product_payload).execute()

    return _row_to_candidate(candidate_row)


@app.get("/suppliers", response_model=list[Supplier])
def list_suppliers() -> list[Supplier]:
    response = (
        supabase_client.table("suppliers")
        .select("id,name,contact_info,shipping_time_days,reliability_score,created_at")
        .execute()
    )
    rows = _response_data(response)
    if rows is None:
        raise HTTPException(status_code=500, detail="Failed to fetch suppliers")
    return [_row_to_supplier(row) for row in rows]


@app.post("/suppliers", response_model=Supplier, status_code=status.HTTP_201_CREATED)
def create_supplier(req: SupplierCreate) -> Supplier:
    payload = {
        "name": req.name,
        "contact_info": req.contact_info,
        "shipping_time_days": req.shipping_time_days,
        "reliability_score": req.reliability_score,
    }
    insert_res = supabase_client.table("suppliers").insert(payload).execute()
    rows = _response_data(insert_res)
    if not rows:
        raise HTTPException(status_code=500, detail="Failed to insert supplier")
    return _row_to_supplier(rows[0])


@app.patch("/suppliers/{supplier_id}", response_model=Supplier)
def update_supplier(supplier_id: int, req: SupplierUpdate) -> Supplier:
    payload: dict[str, Any] = {}

    if req.name is not None:
        payload["name"] = req.name
    if req.contact_info is not None:
        payload["contact_info"] = req.contact_info
    if req.shipping_time_days is not None:
        payload["shipping_time_days"] = req.shipping_time_days
    if req.reliability_score is not None:
        payload["reliability_score"] = req.reliability_score

    if not payload:
        raise HTTPException(status_code=400, detail="No update fields provided")

    supabase_client.table("suppliers").update(payload).eq("id", supplier_id).execute()

    fetch_res = (
        supabase_client.table("suppliers")
        .select("id,name,contact_info,shipping_time_days,reliability_score,created_at")
        .eq("id", supplier_id)
        .single()
        .execute()
    )
    row = _response_data(fetch_res)
    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")

    return _row_to_supplier(row)


@app.get("/orders", response_model=list[Order])
def list_orders() -> list[Order]:
    res = supabase_client.table("orders").select("*").execute()
    rows = _response_data(res)
    if rows is None:
        raise HTTPException(status_code=500, detail="Failed to fetch orders")
    return [_row_to_order(item) for item in rows]


@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(req: OrderCreate) -> Order:
    new_row = {
        "product_id": req.product_id,
        "quantity": req.quantity,
        "status": "pending",
    }
    res = supabase_client.table("orders").insert(new_row).execute()
    rows = _response_data(res)
    if not rows:
        raise HTTPException(status_code=500, detail="Failed to create order")
    return _row_to_order(rows[0])


@app.patch("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, req: OrderUpdate) -> Order:
    update_data: dict[str, Any] = {}

    if req.status is not None:
        update_data["status"] = req.status
    if req.tracking_code is not None:
        update_data["tracking_code"] = req.tracking_code

    if not update_data:
        raise HTTPException(status_code=400, detail="No update fields provided")

    supabase_client.table("orders").update(update_data).eq("id", order_id).execute()

    fetch_res = (
        supabase_client.table("orders")
        .select("*")
        .eq("id", order_id)
        .single()
        .execute()
    )
    updated = _response_data(fetch_res)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")

    return _row_to_order(updated)

 

