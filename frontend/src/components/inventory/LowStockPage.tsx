import { useEffect, useState } from 'react'
import { Package, Truck, AlertTriangle } from 'react-icons/fi'
import { useNavigate } from 'react-router-dom'

type ApiProduct = {
  id: number
  name: string
  sku: string
  category?: string
  stock_count: number
  min_stock: number
  shortfall: number
  status: 'OK' | 'LOW' | 'OUT'
  supplier?: string
}

const reorderSuggestions: Record<string, number> = {
  'USB-C Hub Pro': 30,
  'Office Chair B': 10,
  'Monitor Arm': 15,
  'Standing Desk Pro': 8,
}

export default function LowStockPage() {
  const [products, setProducts] = useState<ApiProduct[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<ApiProduct | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true)
      try {
        const res = await fetch('/api/inventory/products/?status=LOW&status=OUT', { credentials: 'include' })
        if (!res.ok) {
          setProducts([])
          return
        }
        const data = await res.json()
        setProducts(data)
      } catch (err) {
        setProducts([])
      } finally {
        setLoading(false)
      }
    }
    fetchProducts()
  }, [])

  const low = products.filter(p => p.status === 'LOW')
  const out = products.filter(p => p.status === 'OUT')

  const openReceive = (p?: ApiProduct) => {
    if (!p) return navigate('/inventory/receive')
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
    <div className="space-y-5 max-w-[1200px]">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center shrink-0">
            <span className="text-xl">🔴</span>
          </div>
          <div>
            <p className="text-[12px] text-red-700">Out of Stock</p>
            <p className="text-[22px] text-red-700" style={{ fontWeight: 700 }}>{out.length} product{out.length !== 1 ? 's' : ''}</p>
          </div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-yellow-100 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
          </div>
          <div>
            <p className="text-[12px] text-yellow-700">Below Minimum Stock</p>
            <p className="text-[22px] text-yellow-700" style={{ fontWeight: 700 }}>{low.length} product{low.length !== 1 ? 's' : ''}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-border overflow-hidden">
        <div className="px-5 py-3 border-b border-border">
          <h4 className="text-[14px]" style={{ fontWeight: 600 }}>Products Requiring Attention</h4>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-gray-50/50">
              <th className="text-left px-5 py-2.5 text-[12px] text-muted-foreground">Product</th>
              <th className="text-left px-5 py-2.5 text-[12px] text-muted-foreground">SKU</th>
              <th className="text-right px-5 py-2.5 text-[12px] text-muted-foreground">Stock</th>
              <th className="text-right px-5 py-2.5 text-[12px] text-muted-foreground">Min Stock</th>
              <th className="text-right px-5 py-2.5 text-[12px] text-muted-foreground">Reorder Qty</th>
              <th className="text-left px-5 py-2.5 text-[12px] text-muted-foreground">Supplier</th>
              <th className="text-left px-5 py-2.5 text-[12px] text-muted-foreground">Alert</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-b border-border last:border-0 hover:bg-gray-50 cursor-pointer transition-colors" onClick={() => setSelected(p)}>
                <td className="px-5 py-3 text-[13px]" style={{ fontWeight: 500 }}>
                  <div className="flex items-center gap-2"><Package className="w-4 h-4 text-muted-foreground" />{p.name}</div>
                </td>
                <td className="px-5 py-3 text-[13px] text-muted-foreground">{p.sku}</td>
                <td className="px-5 py-3 text-[13px] text-right" style={{ fontWeight: 600, color: p.status === 'OUT' ? '#ef4444' : '#d97706' }}>{p.stock_count}</td>
                <td className="px-5 py-3 text-[13px] text-right text-muted-foreground">{p.min_stock}</td>
                <td className="px-5 py-3 text-[13px] text-right text-muted-foreground">{reorderSuggestions[p.name] ?? 20}</td>
                <td className="px-5 py-3 text-[13px] text-muted-foreground">{p.supplier ?? '-'}</td>
                <td className="px-5 py-3">
                  <span className={`inline-flex px-2 py-0.5 rounded text-[11px] ${p.status === 'OUT' ? 'bg-red-50 text-red-600' : 'bg-yellow-50 text-yellow-700'}`} style={{ fontWeight: 500 }}>
                    {p.status === 'OUT' ? 'Out' : 'Low'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white rounded-xl border border-border p-5">
        <h4 className="text-[14px] mb-4" style={{ fontWeight: 600 }}>Suggested Reorders</h4>
        <div className="space-y-3">
          {products.filter(p => p.status === 'OUT' || p.status === 'LOW').map((p) => (
            <div key={p.id} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
              <div>
                <p className="text-[13px]" style={{ fontWeight: 500 }}>{p.name}</p>
                <p className="text-[12px] text-muted-foreground">{p.supplier ?? '-'} · Reorder {reorderSuggestions[p.name] ?? 20} units</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`inline-flex px-2 py-0.5 rounded text-[11px] ${p.status === 'OUT' ? 'bg-red-50 text-red-600' : 'bg-yellow-50 text-yellow-700'}`} style={{ fontWeight: 500 }}>
                  {p.status === 'OUT' ? 'URGENT' : 'Soon'}
                </span>
                <button className="px-3 py-1.5 bg-[#D1353B] text-white rounded-lg text-[12px] hover:bg-[#b82e33] transition-colors flex items-center gap-1.5" onClick={() => openReceive(p)}>
                  <Truck className="w-3.5 h-3.5" /> Order Now
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
          <div className="absolute inset-0 bg-black opacity-30" onClick={() => setSelected(null)} />
          <div className="bg-white rounded-lg shadow-lg max-w-3xl w-full p-6 z-10 m-4">
            <div className="flex items-start justify-between">
              <h3 style={{ fontWeight: 700 }}>{selected.name}</h3>
              <button onClick={() => setSelected(null)} className="text-muted-foreground">Close</button>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div><span className="text-[11px] text-muted-foreground uppercase tracking-wider">Current Stock</span><p className="text-[20px] mt-0.5" style={{ fontWeight: 700, color: selected.status === 'OUT' ? '#ef4444' : '#d97706' }}>{selected.stock_count}</p></div>
              <div><span className="text-[11px] text-muted-foreground uppercase tracking-wider">Min Required</span><p className="text-[20px] mt-0.5" style={{ fontWeight: 700 }}>{selected.min_stock}</p></div>
              <div><span className="text-[11px] text-muted-foreground uppercase tracking-wider">Supplier</span><p className="text-[13px] mt-0.5">{selected.supplier ?? '-'}</p></div>
              <div><span className="text-[11px] text-muted-foreground uppercase tracking-wider">Reorder Suggestion</span><p className="text-[13px] mt-0.5" style={{ fontWeight: 500 }}>{reorderSuggestions[selected.name] ?? 20} units</p></div>
            </div>
            <div className="mt-6">
              <button className="w-full py-2 bg-[#D1353B] text-white rounded-lg text-[13px] hover:bg-[#b82e33] transition-colors flex items-center justify-center gap-2" onClick={() => { openReceive(selected); setSelected(null) }}>
                <Truck className="w-4 h-4" /> Create Purchase Order
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
