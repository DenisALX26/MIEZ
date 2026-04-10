import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiTruck, FiPackage, FiCheckCircle, FiAlertTriangle, FiArrowDown } from 'react-icons/fi'

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

  const stats = useMemo(() => {
    const total = movements.length
    const inbound = movements.filter(m => String(m.movement_type).toLowerCase().includes('inbound') || String(m.movement_type).toLowerCase().includes('in')).length
    const outbound = total - inbound
    return { total, inbound, outbound }
  }, [movements])

  const handleReceive = (product?: { id: number; name: string; sku: string }) => {
    if (!product) return
    const params = new URLSearchParams({ productId: String(product.id), sku: product.sku ?? '', name: product.name ?? '' })
    navigate(`/inventory/receive?${params.toString()}`)
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Stock Movements</h2>
          <p className="text-sm text-muted-foreground">Recent inbound and outbound stock activity across your inventory</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-[#D1353B] text-white rounded-lg text-[13px] hover:bg-[#b82e33] transition-colors flex items-center gap-2" onClick={() => navigate('/inventory/receive')}>
            <FiArrowDown className="w-4 h-4" /> Receive Stock
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-xl border border-border p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center"><FiPackage className="w-5 h-5 text-muted-foreground" /></div>
          <div>
            <div className="text-sm text-muted-foreground">Total Movements</div>
            <div className="text-lg font-semibold">{stats.total}</div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-border p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center"><FiCheckCircle className="w-5 h-5 text-green-600" /></div>
          <div>
            <div className="text-sm text-muted-foreground">Inbound</div>
            <div className="text-lg font-semibold">{stats.inbound}</div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-border p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center"><FiAlertTriangle className="w-5 h-5 text-red-600" /></div>
          <div>
            <div className="text-sm text-muted-foreground">Outbound</div>
            <div className="text-lg font-semibold">{stats.outbound}</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-border overflow-hidden">
        <div className="px-5 py-3 border-b border-border flex items-center justify-between">
          <h4 className="text-[14px]" style={{ fontWeight: 600 }}>Recent Movements</h4>
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
                    <th className="px-4 py-2">ID</th>
                    <th className="px-4 py-2">Type</th>
                    <th className="px-4 py-2">Product</th>
                    <th className="px-4 py-2">Supplier</th>
                    <th className="px-4 py-2 text-right">Qty</th>
                    <th className="px-4 py-2">Expected</th>
                    <th className="px-4 py-2">Notes</th>
                    <th className="px-4 py-2">Created</th>
                    <th className="px-4 py-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {movements.map(m => {
                    const prod = (m.product_obj ?? (typeof m.product === 'object' ? m.product : null)) as any
                    const supp = (m.supplier_obj ?? (typeof m.supplier === 'object' ? m.supplier : null)) as any
                    const isInbound = String(m.movement_type).toLowerCase().includes('inbound') || String(m.movement_type).toLowerCase().includes('in')
                    return (
                      <tr key={m.id} className="border-t hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{m.id}</td>
                        <td className="px-4 py-3 text-[13px]">{isInbound ? <span className="inline-flex items-center gap-2"><FiArrowDown className="w-4 h-4 text-green-600" />Inbound</span> : <span className="inline-flex items-center gap-2"><FiTruck className="w-4 h-4 text-red-600" />Outbound</span>}</td>
                        <td className="px-4 py-3 text-[13px]" style={{ fontWeight: 500 }}>{prod ? `${prod.name}` : '-'}</td>
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{supp ? supp.name : '-'}</td>
                        <td className="px-4 py-3 text-[13px] text-right font-semibold">{m.quantity}</td>
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{m.expected_date ?? '-'}</td>
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{m.notes ?? '-'}</td>
                        <td className="px-4 py-3 text-[13px] text-muted-foreground">{new Date(m.created_at).toLocaleString()}</td>
                        <td className="px-4 py-3">
                          {prod && isInbound && (
                            <button className="px-3 py-1.5 bg-[#D1353B] text-white rounded-lg text-[12px] hover:bg-[#b82e33] transition-colors" onClick={() => handleReceive(prod)}>
                              <FiTruck className="w-4 h-4 inline-block mr-1 -mt-0.5" /> Receive
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
    </section>
  )
}

export default StockMovementsPage
