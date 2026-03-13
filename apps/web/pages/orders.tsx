import { useState, useEffect } from 'react';

// Adjust the API base URL based on environment. Use NEXT_PUBLIC_API_URL if available, otherwise default to the Render backend URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://ai-dropshipping-app.onrender.com';

// Order type definition
interface Order {
  id: number;
  product_id: number;
  quantity: number;
  status: string;
  tracking_code: string | null;
  created_at: string;
}

// Product type definition (for dropdown selection)
interface Product {
  id: number;
  title: string;
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [status, setStatus] = useState<'loading' | 'error' | 'ok'>('loading');

  // Form state for creating a new order
  const [form, setForm] = useState({
    product_id: '',
    quantity: '',
  });

  // Fetch orders and products when the component mounts
  useEffect(() => {
    async function loadData() {
      try {
        const [ordersRes, productsRes] = await Promise.all([
          fetch(`${API_BASE}/orders`),
          fetch(`${API_BASE}/products`),
        ]);
        const ordersData = await ordersRes.json();
        const productsData = await productsRes.json();
        setOrders(ordersData);
        setProducts(productsData);
        setStatus('ok');
      } catch (err) {
        console.error(err);
        setStatus('error');
      }
    }
    loadData();
  }, []);

  // Handle form submission to create a new order
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const prodId = parseInt(form.product_id, 10);
    const qty = parseInt(form.quantity, 10);
    if (!prodId || !qty || qty < 1) {
      return;
    }
    await fetch(`${API_BASE}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: prodId, quantity: qty }),
    });
    // Reload orders after creation
    const res = await fetch(`${API_BASE}/orders`);
    const data = await res.json();
    setOrders(data);
    // Reset form
    setForm({ product_id: '', quantity: '' });
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h1>Orders</h1>
      <p>Backend status: <strong>{status}</strong></p>

      {/* Form to create a new order */}
      <form onSubmit={handleSubmit} style={{ marginBottom: '2rem' }}>
        <select
          value={form.product_id}
          onChange={(e) => setForm({ ...form, product_id: e.target.value })}
        >
          <option value="">Select product</option>
          {products.map((product) => (
            <option key={product.id} value={product.id}>
              {product.title}
            </option>
          ))}
        </select>
        <input
          type="number"
          placeholder="Quantity"
    import { useState, useEffect } from 'react';

// Adjust the API base URL based on environment. Use NEXT_PUBLIC_API_URL if available, otherwise default to the Render backend URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://ai-dropshipping-app.onrender.com';

// Order type definition
interface Order {
  id: number;
  product_id: number;
  quantity: number;
  status: string;
  tracking_code: string | null;
  created_at: string;
}

// Product type definition (for dropdown selection)
interface Product {
  id: number;
  title: string;
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [status, setStatus] = useState<'loading' | 'error' | 'ok'>('loading');

  // Form state for creating a new order
  const [form, setForm] = useState({
    product_id: '',
    quantity: '',
  });

  // Fetch orders and products when the component mounts
  useEffect(() => {
    async function loadData() {
      try {
        const [ordersRes, productsRes] = await Promise.all([
          fetch(`${API_BASE}/orders`),
          fetch(`${API_BASE}/products`),
        ]);
        const ordersData = await ordersRes.json();
        const productsData = await productsRes.json();
        setOrders(ordersData);
        setProducts(productsData);
        setStatus('ok');
      } catch (err) {
        console.error(err);
        setStatus('error');
      }
    }
    loadData();
  }, []);

  // Handle form submission to create a new order
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const prodId = parseInt(form.product_id, 10);
    const qty = parseInt(form.quantity, 10);
    if (!prodId || !qty || qty < 1) {
      return;
    }
    await fetch(`${API_BASE}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: prodId, quantity: qty }),
    });
    // Reload orders after creation
    const res = await fetch(`${API_BASE}/orders`);
    const data = await res.json();
    setOrders(data);
    // Reset form
    setForm({ product_id: '', quantity: '' });
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h1>Orders</h1>
      <p>Backend status: <strong>{status}</strong></p>

      {/* Form to create a new order */}
      <form onSubmit={handleSubmit} style={{ marginBottom: '2rem' }}>
        <select
          value={form.product_id}
          onChange={(e) => setForm({ ...form, product_id: e.target.value })}
        >
          <option value="">Select product</option>
          {products.map((product) => (
            <option key={product.id} value={product.id}>
              {product.title}
            </option>
          ))}
        </select>
        <input
          type="number"
          placeholder="Quantity"
          min={1}
          value={form.quantity}
          onChange={(e) => setForm({ ...form, quantity: e.target.value })}
          style={{ marginLeft: '0.5rem' }}
        />
        <button type="submit" style={{ marginLeft: '0.5rem' }}>
          Create Order
        </button>
      </form>

      {/* List of orders */}
      {orders.map((order) => (
        <div
          key={order.id}
          style={{ border: '1px solid #ccc', padding: '1rem', marginBottom: '1rem' }}
        >
          <div>
            <strong>Order #{order.id}</strong>
          </div>
          <div>Product ID: {order.product_id}</div>
          <div>Quantity: {order.quantity}</div>
          <div>Status: {order.status}</div>
          {order.tracking_code && <div>Tracking: {order.tracking_code}</div>}
          <div>
            Created at: {new Date(order.created_at).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
      min={1}
          value={form.quantity}
          onChange={(e) => setForm({ ...form, quantity: e.target.value })}
          style={{ marginLeft: '0.5rem' }}
        />
        <button type="submit" style={{ marginLeft: '0.5rem' }}>
          Create Order
        </button>
      </form>

      {/* List of orders */}
      {orders.map((order) => (
        <div
          key={order.id}
          style={{ border: '1px solid #ccc', padding: '1rem', marginBottom: '1rem' }}
        >
          <div>
            <strong>Order #{order.id}</strong>
          </div>
          <div>Product ID: {order.product_id}</div>
          <div>Quantity: {order.quantity}</div>
          <div>Status: {order.status}</div>
          {order.tracking_code && <div>Tracking: {order.tracking_code}</div>}
          <div>
            Created at: {new Date(order.created_at).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
