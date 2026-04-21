import { useEffect, useState } from 'react'
import { FiArrowDownLeft, FiArrowUpRight, FiRefreshCw, FiTrash2, FiBox, FiFilter, FiCalendar } from 'react-icons/fi'
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

const TypeIcon = ({ type }: { type: string }) => {
  const t = (type || '').toUpperCase();
  if (t === 'INBOUND') return <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0"><FiArrowDownLeft size={16} /></div>;
  if (t === 'OUTBOUND') return <div className="w-8 h-8 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center shrink-0"><FiArrowUpRight size={16} /></div>;
  if (t === 'ADJUSTMENT') return <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center shrink-0"><FiRefreshCw size={16} /></div>;
  if (t === 'WRITE_OFF') return <div className="w-8 h-8 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center shrink-0"><FiTrash2 size={16} /></div>;
  return <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center shrink-0"><FiBox size={16} /></div>;
}

const renderQty = (m: Movement) => {
  const t = (m.movement_type || '').toUpperCase()
  if (t === 'INBOUND') return <span className="text-emerald-600 font-semibold text-[1rem]">+{m.quantity}</span>
  if (t === 'OUTBOUND' || t === 'WRITE_OFF') return <span className="text-rose-600 font-semibold text-[1rem]">-{m.quantity}</span>
  if (t === 'ADJUSTMENT') return <span className="text-blue-600 font-semibold text-[1rem]">{m.quantity}</span>
  return <span className="font-semibold text-[1rem]">{m.quantity}</span>
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

  return (
    <div className="max-w-[1400px] mx-auto space-y-8 animate-[fadeIn_0.5s_ease-out] pb-10">
      
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 bg-white p-8 rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/40">
        <div className="flex items-center gap-5">
          <div className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl">
            <FiRefreshCw size={32} strokeWidth={2} />
          </div>
          <div>
            <h1 className="text-[1.18rem] font-semibold text-gray-900 tracking-tight">Stock Movements Registry</h1>
            <p className="text-gray-500 mt-2 font-medium">Complete, transparent ledger of all inbound, outbound, and inventory adjustments.</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:flex gap-3">
           <div className="flex bg-gray-50 p-1.5 rounded-xl border border-gray-200/70 items-center">
             <FiFilter className="text-gray-400 ml-3 mr-2" />
             <select 
               value={typeFilter} 
               onChange={(e) => setTypeFilter(e.target.value)} 
               className="bg-transparent border-none outline-none text-sm font-bold text-gray-700 py-2 pr-4 pl-1 cursor-pointer focus:ring-0"
             >
                <option value="ALL">All Event Types</option>
                <option value="INBOUND">Inbound Flows</option>
                <option value="OUTBOUND">Outbound Drafts</option>
                <option value="ADJUSTMENT">Adjustments</option>
                <option value="WRITE_OFF">Write-offs</option>
             </select>
           </div>
           
           <div className="flex bg-gray-50 p-1.5 rounded-xl border border-gray-200/70 items-center overflow-hidden">
             <FiCalendar className="text-gray-400 ml-3 mr-2 shrink-0" />
             <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="bg-transparent border-none text-xs font-bold text-gray-600 focus:ring-0 w-[110px]" />
             <span className="text-gray-300 font-light px-1">-</span>
             <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="bg-transparent border-none text-xs font-bold text-gray-600 focus:ring-0 w-[110px]" />
           </div>

           <button 
             onClick={() => { setPage(1); fetchData(1); }}
             className="px-6 py-2 bg-gray-900 text-white text-sm font-bold rounded-xl hover:bg-indigo-600 transition-colors shadow-sm"
           >
             Filter
           </button>
           
           {(typeFilter !== 'ALL' || dateFrom || dateTo) && (
              <button 
                onClick={() => { setTypeFilter('ALL'); setDateFrom(''); setDateTo(''); fetchData(1); }}
                className="px-4 py-2 border border-gray-200 text-gray-600 text-sm font-bold rounded-xl hover:bg-gray-100 transition-colors"
               >
                Reset
               </button>
           )}
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/40 relative overflow-hidden">
        
        {loading && (
          <div className="absolute inset-0 bg-white/60 backdrop-blur-sm z-10 flex flex-col items-center justify-center">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-4" />
            <p className="font-bold text-gray-400 tracking-widest text-sm uppercase">Synchronizing Ledger...</p>
          </div>
        )}

        <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
          <h4 className="text-[1rem] font-semibold text-gray-900 tracking-tight">Movement History</h4>
          <span className="inline-flex px-3 py-1 bg-indigo-100 text-indigo-700 text-xs font-bold rounded-lg">{count} Records Found</span>
        </div>

        {movements.length === 0 && !loading ? (
             <div className="text-center py-24">
                <FiRefreshCw size={48} className="mx-auto text-gray-200 mb-4" />
                <h3 className="text-xl font-black text-gray-400">No log entries</h3>
                <p className="text-gray-400 mt-2">Adjust your filters or add some stock to see activity.</p>
             </div>
        ) : (
          <div className="overflow-x-auto min-h-[400px]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white border-b border-gray-100">
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap">EventType</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap">Subject Product</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap text-right">Modifier Qty</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap">Partner Identity</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap">Timestamp & Operator</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap">Controls</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {movements.map((m) => {
                  const prodName = m.product_name || (m.product_obj && m.product_obj.name) || 'Unknown Item'
                  const sku = m.product_sku || (m.product_obj && m.product_obj.sku) || 'NO-SKU'
                  const supplier = m.supplier_name || (m.supplier_obj && m.supplier_obj.name) || '-'
                  const dateObj = new Date(m.created_at)

                  return (
                    <tr key={m.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-8 py-5">
                         <div className="flex items-center gap-3">
                           <TypeIcon type={m.movement_type} />
                           <span className="text-xs font-bold text-gray-700 tracking-wider uppercase">{m.movement_type.replace('_', '-')}</span>
                         </div>
                      </td>
                      <td className="px-8 py-5">
                         <div>
                            <p className="font-bold text-gray-900 text-sm">{prodName}</p>
                            <span className="text-[11px] bg-gray-100 px-2 py-0.5 rounded text-gray-500 font-mono tracking-wider">{sku}</span>
                         </div>
                      </td>
                      <td className="px-8 py-5 text-right">
                         {renderQty(m)}
                      </td>
                      <td className="px-8 py-5">
                        <span className={`text-[13px] ${supplier === '-' ? 'text-gray-400 italic' : 'font-medium text-gray-700'}`}>{supplier}</span>
                      </td>
                      <td className="px-8 py-5">
                         <div>
                           <p className="text-sm font-semibold text-gray-900">{dateObj.toLocaleDateString()} <span className="text-gray-400 font-normal">{dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span></p>
                           <p className="text-[11px] text-gray-500 font-medium tracking-wide">By {m.created_by_username || 'System'}</p>
                         </div>
                      </td>
                      <td className="px-8 py-5">
                        {(m.product_obj || (typeof m.product === 'object' && m.product)) && (m.movement_type || '').toUpperCase() === 'INBOUND' ? (
                          <button 
                            className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-xl text-[12px] font-bold hover:bg-indigo-600 hover:text-white transition-all shadow-sm"
                            onClick={() => handleReceive((m.product_obj as any) || (m.product as any))}
                          >
                            Execute Receipt
                          </button>
                        ) : (
                          <span className="text-gray-300 text-xl font-light">…</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Pagination Controls */}
        <div className="p-6 border-t border-gray-100 bg-gray-50/50 flex items-center justify-between">
           <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">
             Showing Page {page}
           </p>
           <div className="flex items-center gap-2">
             <button 
               disabled={page <= 1} 
               onClick={() => { setPage((s) => Math.max(1, s-1)); fetchData(page-1); }} 
               className="p-2 border border-gray-200 bg-white rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-gray-600"
              >
               <FiArrowDownLeft className="rotate-45" />
             </button>
             <button 
               disabled={movements.length < 20} // Assuming 20 is the default page size configured in backend
               onClick={() => { setPage((s) => s+1); fetchData(page+1); }} 
               className="p-2 border border-gray-200 bg-white rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-gray-600"
              >
               <FiArrowUpRight className="rotate-45" />
             </button>
           </div>
        </div>
      </div>
    </div>
  )
}

