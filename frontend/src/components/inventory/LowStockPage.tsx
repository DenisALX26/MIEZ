import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type Product = {
  id: number
  name: string
  sku: string
  category: string
  stock_count: number
  min_stock: number
  shortfall: number
  status: 'OK' | 'LOW' | 'OUT'
}

const LowStockPage = () => {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true)
      try {
        const resp = await fetch('/api/inventory/products/?status=LOW&status=OUT', { credentials: 'include' })
        if (!resp.ok) {
          setProducts([])
          setLoading(false)
          return
        }
        const data = await resp.json()
        setProducts(data)
      } catch {
        setProducts([])
      } finally {
        setLoading(false)
      }
    }
    fetchProducts()
  }, [])

  const handleReceive = (p: Product) => {
    // Navigate to receive form (prefill via query params)
    const params = new URLSearchParams({ productId: String(p.id), sku: p.sku, name: p.name })
    navigate(`/inventory/receive?${params.toString()}`)
  }

  if (loading) return <div>Loading...</div>

  if (products.length === 0) {
    return (
      <div className="module-card text-center">
        <div className="text-green-500 text-6xl">✓</div>
        <h2 className="mt-4">All products are within safe stock levels</h2>
        <p className="text-muted mt-2">No action required right now.</p>
      </div>
    )
  }

  return (
    <section>
      <h2>At-risk products</h2>
      <div className="card">
        <table className="inventory-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>SKU</th>
              <th>Category</th>
              <th>Current Stock</th>
              <th>Min Stock</th>
              <th>Shortfall</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {products.map(p => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.sku}</td>
                <td>{p.category}</td>
                <td>{p.stock_count}</td>
                <td>{p.min_stock}</td>
                <td>
                  <span
                    className={
                      p.status === 'OUT'
                        ? 'shortfall-badge shortfall-out'
                        : 'shortfall-badge shortfall-low'
                    }
                  >
                    {p.shortfall > 0 ? p.shortfall : 0}
                  </span>
                </td>
                <td>
                  <button className="btn" onClick={() => handleReceive(p)}>
                    Receive Stock
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default LowStockPage
