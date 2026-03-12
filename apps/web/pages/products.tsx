import { useEffect, useState } from "react";

// Base URL of the backend API.  If NEXT_PUBLIC_API_URL is set in
// your Vercel environment, it will override this default.  Otherwise
// it falls back to the Render domain used in development.
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://ai-dropshipping-app.onrender.com";

interface Product {
  id: number;
  title: string;
  cost_price: number;
  sale_price: number;
  score?: number | null;
  status?: string | null;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [status, setStatus] = useState("loading");

  async function loadProducts() {
    try {
      const res = await fetch(`${API_BASE}/products`);
      const data = await res.json();
      setProducts(data);
      setStatus("ok");
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  }

  useEffect(() => {
      loadProducts();
  }, []);

  async function publishProduct(id: number) {
    try {
      const res = await fetch(`${API_BASE}/products/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "published" }),
      });
      if (res.ok) {
        // Reload the product list after updating
        loadProducts();
      } else {
        console.error(await res.text());
      }
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div style={{ padding: "1rem" }}>
      <h1>Prodotti</h1>
      <p>Stato backend: <strong>{status}</strong></p>
      {products.map((p) => (
        <div key={p.id} style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem" }}>
          <strong>{p.title}</strong><br />
          Costo: €{p.cost_price}<br />
          Prezzo vendita: €{p.sale_price}<br />
          Score: {p.score ?? "-"}<br />
          Stato: {p.status ?? "-"}<br />
          {p.status !== "published" && (
            <button onClick={() => publishProduct(p.id)}>
              Pubblica
            </button>
          )}
        </div>
      ))}
    </div>
  );
}