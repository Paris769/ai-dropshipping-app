import { useEffect, useState, FormEvent } from "react";

/*
 * Candidates page
 *
 * This page lists all product candidates and provides a form for adding a
 * new candidate.  Candidates are proposed products that have been scored
 * but not yet approved for listing in the main catalogue.  Supervisors
 * can use this page to review and triage candidate ideas.
 */

// Default API base points at the Render deployment.  In production you
// may override this via an environment variable NEXT_PUBLIC_API_URL to
// support staging vs production backends.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://ai-dropshipping-app.onrender.com";

type Candidate = {
  id: number;
  title: string;
  source?: string | null;
  supplier_url?: string | null;
  category?: string | null;
  cost_price: number;
  suggested_sale_price?: number | null;
  score: number;
  status: string;
  notes?: string | null;
  created_at: string;
};

export default function CandidatesPage() {
  const [items, setItems] = useState<Candidate[]>([]);
  const [status, setStatus] = useState("loading");
  const [form, setForm] = useState({
    title: "",
    source: "",
    supplier_url: "",
    category: "",
    cost_price: "",
    notes: "",
  });

  // Fetch candidates from the backend
  async function loadCandidates() {
    try {
      const res = await fetch(`${API_BASE}/product-candidates`);
      if (!res.ok) throw new Error("Request failed");
      const data = await res.json();
      setItems(data);
      setStatus("ok");
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  }

  useEffect(() => {
    loadCandidates();
  }, []);

  // Handle form submission for adding a candidate
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      const payload = {
        title: form.title,
        source: form.source || null,
        supplier_url: form.supplier_url || null,
        category: form.category || null,
        cost_price: parseFloat(form.cost_price),
        notes: form.notes || null,
      };
      const res = await fetch(`${API_BASE}/product-candidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Create candidate failed");
      // Reset form and reload list
      setForm({ title: "", source: "", supplier_url: "", category: "", cost_price: "", notes: "" });
      loadCandidates();
    } catch (err) {
      console.error(err);
      alert("Errore durante la creazione del candidato.");
    }
  }

  // Update candidate status (e.g. approve or reject)
  async function updateCandidateStatus(id: number, newStatus: string) {
    try {
      const res = await fetch(`${API_BASE}/product-candidates/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error("Update candidate failed");
      // Reload list after successful update
      loadCandidates();
    } catch (err) {
      console.error(err);
      alert("Errore durante l'aggiornamento dello stato del candidato.");
    }
  }

  return (
    <div style={{ padding: "1rem", maxWidth: "800px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>Candidati Prodotti</h1>
      <p style={{ marginBottom: "1rem" }}>
        Stato backend: <strong>{status}</strong>
      </p>
      {/* Form for new candidate */}
      <form onSubmit={handleSubmit} style={{ marginBottom: "2rem", display: "grid", gap: "0.5rem" }}>
        <input
          type="text"
          placeholder="Titolo prodotto"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
        />
        <input
          type="text"
          placeholder="Fonte (es. TikTok)"
          value={form.source}
          onChange={(e) => setForm({ ...form, source: e.target.value })}
        />
        <input
          type="text"
          placeholder="URL fornitore"
          value={form.supplier_url}
          onChange={(e) => setForm({ ...form, supplier_url: e.target.value })}
        />
        <input
          type="text"
          placeholder="Categoria"
          value={form.category}
          onChange={(e) => setForm({ ...form, category: e.target.value })}
        />
        <input
          type="number"
          step="0.01"
          placeholder="Costo"
          value={form.cost_price}
          onChange={(e) => setForm({ ...form, cost_price: e.target.value })}
          required
        />
        <input
          type="text"
          placeholder="Note"
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
        />
        <button type="submit" style={{ padding: "0.5rem 1rem", cursor: "pointer" }}>Aggiungi candidato</button>
      </form>
      {/* List of candidates */}
      {items.map((item) => (
        <div key={item.id} style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem", borderRadius: "4px" }}>
          <h2 style={{ margin: "0 0 0.5rem 0", fontSize: "1.2rem" }}>{item.title}</h2>
          <p>Fonte: {item.source || "-"}</p>
          <p>Categoria: {item.category || "-"}</p>
          <p>Costo: {item.cost_price} €</p>
          <p>Prezzo suggerito: {item.suggested_sale_price != null ? `${item.suggested_sale_price} €` : "-"}</p>
          <p>Score: {item.score}/100</p>
          <p>Stato: {item.status}</p>
          <p>Note: {item.notes || "-"}</p>
          <p style={{ fontSize: "0.8rem", color: "#666" }}>Creato il {new Date(item.created_at).toLocaleString()}</p>
          {/* Action buttons for approving or rejecting a candidate */}
          <div style={{ marginTop: "0.5rem" }}>
            <button
              onClick={() => updateCandidateStatus(item.id, "approved")}
              disabled={item.status === "approved"}
              style={{ marginRight: "0.5rem", padding: "0.3rem 0.6rem", cursor: item.status === "approved" ? "default" : "pointer" }}
            >
              Approva
            </button>
            <button
              onClick={() => updateCandidateStatus(item.id, "rejected")}
              disabled={item.status === "rejected"}
              style={{ padding: "0.3rem 0.6rem", cursor: item.status === "rejected" ? "default" : "pointer" }}
            >
              Rifiuta
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}