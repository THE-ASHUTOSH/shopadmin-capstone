import { useEffect, useState } from 'react'

const empty = { name: '', sku: '', category: 'General', price: '', stock: '' }
const money = (n) => '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 })

async function api(path, options = {}) {
  const res = await fetch('/api/products' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${res.status})`)
  }
  return res.status === 204 ? null : res.json()
}

export default function App() {
  const [products, setProducts] = useState([])
  const [stats, setStats] = useState(null)
  const [q, setQ] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(null)

  async function load() {
    try {
      const params = new URLSearchParams({ q, category })
      const [list, s] = await Promise.all([api('?' + params), api('/stats')])
      setProducts(list)
      setStats(s)
      setError('')
    } catch (e) {
      setError('Could not reach the backend. ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [q, category])

  async function submit(e) {
    e.preventDefault()
    const { id, error, created_at, ...data } = form
    const body = JSON.stringify({ ...data, price: Number(data.price), stock: Number(data.stock || 0) })
    try {
      if (id) await api('/' + id, { method: 'PUT', body })
      else await api('', { method: 'POST', body })
      setForm(null)
      load()
    } catch (e) {
      setForm({ ...form, error: e.message })
    }
  }

  async function remove(p) {
    if (!confirm(`Delete ${p.name}?`)) return
    await api('/' + p.id, { method: 'DELETE' }).catch((e) => setError(e.message))
    load()
  }

  const categories = [...new Set(products.map((p) => p.category))]
  const field = (key) => ({ value: form[key], onChange: (e) => setForm({ ...form, [key]: e.target.value }) })

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>ShopAdmin</h1>
        <nav>
          <a className="active">Products</a>
          <a>Orders</a>
          <a>Customers</a>
        </nav>
      </aside>

      <main>
        <header>
          <div>
            <h2>Products</h2>
            <p className="muted">Manage your store catalogue and stock</p>
          </div>
          <button onClick={() => setForm(empty)}>+ Add product</button>
        </header>

        {error && <div className="error">{error}</div>}

        <section className="cards">
          <div className="card"><span>Total products</span><b>{stats?.total ?? '-'}</b></div>
          <div className="card warn"><span>Low stock</span><b>{stats?.low_stock ?? '-'}</b></div>
          <div className="card"><span>Categories</span><b>{stats?.categories ?? '-'}</b></div>
          <div className="card"><span>Inventory value</span><b>{stats ? money(stats.inventory_value) : '-'}</b></div>
        </section>

        <section className="panel">
          <div className="toolbar">
            <input placeholder="Search name or SKU" value={q} onChange={(e) => setQ(e.target.value)} />
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">All categories</option>
              {categories.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>

          {loading ? <p className="muted">Loading...</p> : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Name</th><th>SKU</th><th>Category</th><th>Price</th><th>Stock</th><th></th></tr>
                </thead>
                <tbody>
                  {products.map((p) => (
                    <tr key={p.id}>
                      <td>{p.name}</td>
                      <td className="muted">{p.sku}</td>
                      <td>{p.category}</td>
                      <td>{money(p.price)}</td>
                      <td><span className={p.stock < 10 ? 'badge low' : 'badge'}>{p.stock}</span></td>
                      <td className="actions">
                        <button className="ghost" onClick={() => setForm({ ...p })}>Edit</button>
                        <button className="ghost danger" onClick={() => remove(p)}>Delete</button>
                      </td>
                    </tr>
                  ))}
                  {products.length === 0 && <tr><td colSpan="6" className="muted center">No products yet</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      {form && (
        <div className="overlay" onClick={() => setForm(null)}>
          <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
            <h3>{form.id ? 'Edit product' : 'New product'}</h3>
            {form.error && <div className="error">{form.error}</div>}
            <label>Name<input required {...field('name')} /></label>
            <label>SKU<input required {...field('sku')} /></label>
            <label>Category<input {...field('category')} /></label>
            <div className="row">
              <label>Price<input required type="number" min="0" step="0.01" {...field('price')} /></label>
              <label>Stock<input type="number" min="0" {...field('stock')} /></label>
            </div>
            <div className="row end">
              <button type="button" className="ghost" onClick={() => setForm(null)}>Cancel</button>
              <button>Save</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
