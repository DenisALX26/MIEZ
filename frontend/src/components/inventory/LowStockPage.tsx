import { useEffect, useState } from 'react'
import { FiTruck, FiAlertCircle, FiBox } from 'react-icons/fi'
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

export default function LowStockPage() {
  const [products, setProducts] = useState<ApiProduct[]>([])
  const [loading, setLoading] = useState(true)
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

  const openReceive = (p: ApiProduct) => {
    const params = new URLSearchParams({ productId: String(p.id), sku: p.sku, name: p.name })
    navigate(`/inventory/receive-stock?${params.toString()}`)
  }

  if (loading) return null

  if (products.length === 0) {
    return (
      <div className="max-w-[700px] mx-auto mt-20 p-12 bg-white rounded-3xl border border-gray-100 shadow-sm text-center">
        <div className="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6 text-emerald-500 border border-emerald-100">
           <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
        </div>
        <h2 className="text-2xl font-black text-gray-900 tracking-tight">All products are within safe stock levels</h2>
        <p className="text-gray-500 mt-2 font-medium">Your inventory is healthy. No stock replenishments are required at this time.</p>
      </div>
    )
  }

  const outCount = products.filter(p => p.status === 'OUT').length;

  return (
    <div className="max-w-[1400px] mx-auto space-y-8 pb-10">
      {/* Header exactly like Dashboard */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-gray-200 pb-6">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Critical Stock Alerts</h1>
          <p className="text-gray-500 mt-1 font-medium">Review and replenish products that have fallen below safety limits.</p>
        </div>
        <div className="flex items-center gap-3">
          {outCount > 0 && (
            <span className="px-4 py-2 bg-rose-50 text-rose-700 font-bold rounded-xl border border-rose-100 flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
              </span>
              {outCount} Depleted
            </span>
          )}
          <span className="px-4 py-2 bg-white text-gray-700 font-bold rounded-xl border border-gray-200 flex items-center gap-2 shadow-sm">
            <FiBox className="text-indigo-500" />
            {products.length} Affected
          </span>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        
        {/* Table Header Row */}
        <div className="px-6 py-5 flex items-center justify-between border-b border-gray-200 bg-gray-50/30">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
              <FiAlertCircle size={20} />
            </div>
            <h4 className="text-lg font-black text-gray-900 tracking-tight">Products Requiring Attention</h4>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-widest w-[30%]">Product Details</th>
                <th className="px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-widest text-center bg-gray-50/30">Current</th>
                <th className="px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-widest text-center">Minimum</th>
                <th className="px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-widest text-center">Shortfall</th>
                <th className="px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-widest text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {products.map((p) => {
                const shortfall = Math.max(0, p.min_stock - p.stock_count)
                const isOut = p.status === 'OUT'
                return (
                  <tr key={p.id} className="hover:bg-slate-50 transition-colors group">
                    <td className="px-6 py-4">
                      <p className="font-bold text-gray-900 text-[15px]">{p.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-400 font-mono bg-gray-100 px-1.5 py-0.5 rounded">{p.sku}</span>
                        {p.category && <span className="text-[11px] font-bold text-indigo-500 uppercase tracking-wider">{p.category}</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center bg-gray-50/10 group-hover:bg-transparent transition-colors">
                      <span className={`text-[22px] font-black ${isOut ? 'text-rose-600' : 'text-amber-500'}`}>{p.stock_count}</span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="text-[15px] font-bold text-gray-400">{p.min_stock}</span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-wider ${isOut ? 'bg-rose-50 text-rose-600 border border-rose-200' : 'bg-amber-50 text-amber-600 border border-amber-200'}`}>
                        -{shortfall} units
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => openReceive(p)}
                        className="px-6 py-2.5 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-slate-800 hover:shadow-lg hover:-translate-y-0.5 transition-all inline-flex items-center gap-2"
                      >
                        <FiTruck size={14} /> Refill Stock
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
