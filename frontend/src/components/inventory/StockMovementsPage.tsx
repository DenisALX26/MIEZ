import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type Movement = {
  id: number
  movement_type: string
  product?: number | { id: number; name: string; sku: string }
  product_obj?: { id: number; name: string; sku: string }
  product_name?: string
  product_sku?: string
  supplier?: number | { id: number; name: string }
  supplier_obj?: { id: number; name: string }
  supplier_name?: string
  quantity: number
  expected_date?: string | null
  notes?: string
  created_by?: number
  created_by_username?: string
  created_at: string
}

type PaginatedResponse = {
  count: number
  next: string | null
  previous: string | null
  results: Movement[]
}

export default function StockMovementsPage() {
  const [movements, setMovements] = useState<Movement[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const navigate = useNavigate()

  const fetchData = async (p = 1) => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.set('page', String(p))
      if (typeFilter && typeFilter !== 'ALL') params.append('type', typeFilter)
      if (dateFrom) params.set('date_from', dateFrom)
      if (dateTo) params.set('date_to', dateTo)

      const res = await fetch(`/api/inventory/stock-movements/?${params.toString()}`, { credentials: 'include' })
      if (!res.ok) {
        setMovements([])
        setCount(0)
        setLoading(false)
        return
      }

      const data: PaginatedResponse = await res.json()
      setMovements(data.results || data)
      setCount(data.count ?? 0)
    } catch (err) {
      setMovements([])
      setCount(0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData(page) /* eslint-disable-line react-hooks/exhaustive-deps */ }, [page])

  const handleReceive = (prod?: { id: number; name: string; sku: string }) => {
    if (!prod) return
    const params = new URLSearchParams({ productId: String(prod.id), sku: prod.sku ?? '', name: prod.name ?? '' })
    navigate(`/inventory/receive?${params.toString()}`)
  }

  const badgeForType = (t?: string) => {
    const tv = (t || '').toUpperCase()
    if (tv === 'INBOUND') return <span className="px-2 py-0.5 rounded text-xs bg-green-50 text-green-700">Inbound</span>
    if (tv === 'OUTBOUND') return <span className="px-2 py-0.5 rounded text-xs bg-orange-50 text-orange-700">Outbound</span>
    if (tv === 'ADJUSTMENT') return <span className="px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700">Adjustment</span>
    if (tv === 'WRITE_OFF') return <span className="px-2 py-0.5 rounded text-xs bg-red-50 text-red-700">Write-off</span>
    return <span className="px-2 py-0.5 rounded text-xs bg-gray-50 text-muted-foreground">{t}</span>
  }

  const renderQty = (m: Movement) => {
    const t = (m.movement_type || '').toUpperCase()
    if (t === 'INBOUND') return <span className="text-green-600 font-semibold">+{m.quantity}</span>
    if (t === 'OUTBOUND' || t === 'WRITE_OFF') return <span className="text-red-600 font-semibold">-{m.quantity}</span>
    if (t === 'ADJUSTMENT') return <span className="text-blue-600 font-semibold">{m.quantity}</span>
    return <span className="font-semibold">{m.quantity}</span>
  }

  return (
    <div className="space-y-4 max-w-[1200px]">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Stock Movements</h2>
          <p className="text-sm text-muted-foreground">Full history of inbound/outbound/adjustments for auditing</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); fetchData(1); }} className="px-3 py-2 border border-border rounded-lg bg-white text-sm">
            <option value="ALL">All types</option>
            <option value="INBOUND">Inbound</option>
            <option value="OUTBOUND">Outbound</option>
            <option value="ADJUSTMENT">Adjustment</option>
            <option value="WRITE_OFF">Write-off</option>
          </select>
          <input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }} className="px-2 py-2 border border-border rounded-lg text-sm" />
          <input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }} className="px-2 py-2 border border-border rounded-lg text-sm" />
          <button className="px-3 py-2 bg-[#D1353B] text-white rounded-lg text-sm" onClick={() => fetchData(1)}>Apply</button>
          <button className="px-3 py-2 border border-border rounded-lg text-sm" onClick={() => { setTypeFilter('ALL'); setDateFrom(''); setDateTo(''); fetchData(1); }}>Reset</button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-border overflow-hidden">
        <div className="px-5 py-3 border-b border-border">
          <h4 className="text-[14px] font-semibold">Movement History</h4>
        </div>
        <div className="p-4">
          {loading ? (
            <div>Loading...</div>
          ) : movements.length === 0 ? (
            <div className="text-center py-6">No stock movements found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left">
                <thead>
                  <tr className="text-[12px] text-muted-foreground">
                    <th className="px-4 py-2">Date</th>
                    <th className="px-4 py-2">Product</th>
                    <th className="px-4 py-2">SKU</th>
                    <th className="px-4 py-2">Type</th>
                    <th className="px-4 py-2 text-right">Qty</th>
                    <th className="px-4 py-2">Supplier</th>
                    <th className="px-4 py-2">Created By</th>
                    <th className="px-4 py-2">Notes</th>
                    <th className="px-4 py-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {movements.map((m) => {
                    const prodName = m.product_name || (m.product_obj && m.product_obj.name) || '-'
                    const sku = m.product_sku || (m.product_obj && m.product_obj.sku) || '-'
                    const supplier = m.supplier_name || (m.supplier_obj && m.supplier_obj.name) || '-'
                    return (
                      <tr key={m.id} className="border-t hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{new Date(m.created_at).toLocaleString()}</td>
                        <td className="px-4 py-3 text-[13px] font-medium">{prodName}</td>
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{sku}</td>
                        <td className="px-4 py-3">{badgeForType(m.movement_type)}</td>
                        <td className="px-4 py-3 text-[13px] text-right">{renderQty(m)}</td>
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{supplier}</td>
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{m.created_by_username ?? '-'}</td>
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{m.notes ?? '-'}</td>
                        <td className="px-4 py-3">
                          {(m.product_obj || (typeof m.product === 'object' && m.product)) && (m.movement_type || '').toUpperCase() === 'INBOUND' && (
                            <button className="px-3 py-1.5 bg-[#D1353B] text-white rounded-lg text-[12px] hover:bg-[#b82e33] transition-colors" onClick={() => handleReceive((m.product_obj as any) || (m.product as any))}>
                              Receive
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">Total: {count}</div>
        <div className="flex items-center gap-2">
          <button disabled={page <= 1} onClick={() => { setPage((s) => Math.max(1, s-1)); fetchData(page-1); }} className="px-3 py-1 border rounded">Prev</button>
          <span className="px-2">Page {page}</span>
          <button disabled={movements.length === 0} onClick={() => { setPage((s) => s+1); fetchData(page+1); }} className="px-3 py-1 border rounded">Next</button>
        </div>
      </div>
    </div>
  )
}

