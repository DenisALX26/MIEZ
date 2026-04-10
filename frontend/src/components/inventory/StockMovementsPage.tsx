import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type Movement = {
  id: number
  movement_type: string
  product?: number | { id: number; name: string; sku: string }
  product_obj?: { id: number; name: string; sku: string }
  supplier?: number | { id: number; name: string }
  supplier_obj?: { id: number; name: string }
  quantity: number
  expected_date?: string | null
  notes?: string
  created_at: string
}

const StockMovementsPage = () => {
  const [movements, setMovements] = useState<Movement[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchMovements = async () => {
      setLoading(true)
      try {
        const res = await fetch('/api/inventory/stock-movements/', { credentials: 'include' })
        if (!res.ok) {
          setMovements([])
          setLoading(false)
          return
        }
        const data = await res.json()
        setMovements(data)
      } catch (e) {
        setMovements([])
      }
      setLoading(false)
    }
    fetchMovements()
  }, [])

  const handleReceive = (product?: { id: number; name: string; sku: string }) => {
    if (!product) return
    const params = new URLSearchParams({ productId: String(product.id), sku: product.sku ?? '', name: product.name ?? '' })
    navigate(`/inventory/receive?${params.toString()}`)
  }

  return (
    <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Stock Movements</h2>
        <div>
          <button className="btn" onClick={() => navigate('/inventory/receive')}>Receive Stock</button>
        </div>
      </div>

      <div className="mt-4">
        {loading ? (
          <div>Loading...</div>
        ) : movements.length === 0 ? (
          <div>No stock movements found.</div>
        ) : (
          <table className="min-w-full text-left">
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Product</th>
                <th>Supplier</th>
                <th>Quantity</th>
                <th>Expected</th>
                <th>Notes</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {movements.map(m => (
                <tr key={m.id} className="border-t">
                  <td>{m.id}</td>
                  <td>{m.movement_type}</td>
                  <td>{(m.product_obj && `${m.product_obj.name} (${m.product_obj.sku})`) || (typeof m.product === 'object' ? `${m.product.name} (${(m.product as any).sku})` : '-')}</td>
                  <td>{(m.supplier_obj && m.supplier_obj.name) || (typeof m.supplier === 'object' ? (m.supplier as any).name : '-')}</td>
                  <td>{m.quantity}</td>
                  <td>{m.expected_date ?? '-'}</td>
                  <td>{m.notes ?? '-'}</td>
                  <td>{new Date(m.created_at).toLocaleString()}</td>
                  <td>
                    {(m.product_obj || (typeof m.product === 'object' && m.product)) && (
                      <button className="btn" onClick={() => handleReceive((m.product_obj as any) || (m.product as any))}>
                        Receive Stock
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

export default StockMovementsPage
