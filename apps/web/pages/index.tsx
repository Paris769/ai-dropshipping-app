import { useEffect, useState } from 'react';

// Define the shape of a product returned by the API.  This mirrors the
// schema defined in the backend ``Product`` model.  If you add new
// fields to the backend, update this type accordingly.
type Product = {
  id: number;
  title: string;
  cost_price: number;
  sale_price: number;
  score?: number | null;
};

// Use an environment variable for the API base URL if provided.  When
// deploying on Vercel you can define ``NEXT_PUBLIC_API_URL`` in the
// project settings to point at your Render backend (for example
// ``https://ai-dropshipping-app.onrender.com``).  If no variable is
// configured, fall back to the public Render URL directly.  Note that
// the trailing slash is not required.
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  'https://ai-dropshipping-app.onrender.com';

export default function Home() {
  const [status, setStatus] = useState<string>('loading');
  const [products, setProducts] = useState<Product[]>([]);
  const [newProduct, setNewProduct] = useState({
    title: '',
    cost_price: '',
    sale_price: '',
  });

  // Fetch the list of products from the backend when the page loads.
  useEffect(() => {
    async function fetchProducts() {
      try {
        const res = await fetch(`${API_BASE}/products`);
        if (res.ok) {
          const data = await res.json();
          setProducts(data);
          setStatus('ok');
        } else {
          setStatus('error');
        }
      } catch (err) {
        setStatus('error');
      }
    }
    fetchProducts();
  }, []);

  // Handle changes in the new product form fields.  We store the inputs as
  // strings and let the backend validate numeric fields.
  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    setNewProduct((prev) => ({ ...prev, [name]: value }));
  }

  // Submit a new product to the backend.  On success, reload the list and
  // clear the form.  Error handling is minimal for brevity.
  async function handleCreateProduct(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newProduct.title,
          cost_price: parseFloat(newProduct.cost_price),
          sale_price: parseFloat(newProduct.sale_price),
        }),
      });
      if (res.ok) {
        const created = await res.json();
        setProducts((prev) => [...prev, created]);
        setNewProduct({ title: '', cost_price: '', sale_price: '' });
      } else {
        console.error('Error creating product');
      }
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
        AI Dropshipping Control Panel
      </h1>
      <p>
        Backend status: <strong>{status}</strong>
      </p>
      {status === 'ok' && (
        <>
          <h2 style={{ fontSize: '1.25rem', marginTop: '1rem' }}>
            Prodotti disponibili
          </h2>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {products.map((p) => (
              <li
                key={p.id}
                style={{
                  marginBottom: '0.5rem',
                  padding: '0.5rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                }}
              >
                <strong>{p.title}</strong> — costo {p.cost_price} €, prezzo {p.sale_price}
              </li>
            ))}
          </ul>
          <h2 style={{ fontSize: '1.25rem', marginTop: '1rem' }}>
            Aggiungi nuovo prodotto
          </h2>
          <form onSubmit={handleCreateProduct} style={{ marginTop: '0.5rem' }}>
            <div style={{ marginBottom: '0.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                Titolo
              </label>
              <input
                type="text"
                name="title"
                value={newProduct.title}
                onChange={handleInputChange}
                required
                style={{ width: '100%', padding: '0.25rem' }}
              />
            </div>
            <div style={{ marginBottom: '0.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                Prezzo di costo (€)
              </label>
              <input
                type="number"
                step="0.01"
                name="cost_price"
                value={newProduct.cost_price}
                onChange={handleInputChange}
                required
                style={{ width: '100%', padding: '0.25rem' }}
              />
            </div>
            <div style={{ marginBottom: '0.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>
                Prezzo di vendita (€)
              </label>
              <input
                type="number"
                step="0.01"
                name="sale_price"
                value={newProduct.sale_price}
                onChange={handleInputChange}
                required
                style={{ width: '100%', padding: '0.25rem' }}
              />
            </div>
            <button
              type="submit"
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#0070f3',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Aggiungi prodotto
            </button>
          </form>
        </>
      )}
    </div>
  );
}