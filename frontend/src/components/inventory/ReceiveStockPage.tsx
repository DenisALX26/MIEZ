import { useEffect, useState } from 'react'
import { FiArrowDown, FiCheckCircle, FiTruck, FiPackage, FiSearch, FiCalendar } from 'react-icons/fi'

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

type Product = {
  id: number
  name: string
  sku: string
}

export default function ReceiveStockPage() {
  const [showForm, setShowForm] = useState(false)
  const [products, setProducts] = useState<Product[]>([])
  const [suppliers, setSuppliers] = useState<Array<{ id: number; name: string }>>([])

  const [form, setForm] = useState({ product: '', supplier: '', qty: '', expected_date: '', notes: '' })
  const [submitted, setSubmitted] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const [search, setSearch] = useState('')

  const [recentDeliveries, setRecentDeliveries] = useState<Movement[]>([])
  const [loadingDeliveries, setLoadingDeliveries] = useState(true)

  const fetchDeliveries = async () => {
    setLoadingDeliveries(true)
    try {
      const res = await fetch('/api/inventory/stock-movements/?type=INBOUND', { credentials: 'include' })
      if (res.ok) {
        const data = await res.json()
        setRecentDeliveries(data.results || data)
      }
    } catch (err) {
      // ignore
    } finally {
      setLoadingDeliveries(false)
    }
  }

  useEffect(() => {
    fetchDeliveries()

    // Fetch products for dropdown
    fetch('/api/inventory/products/', { credentials: 'include' })
      .then(r => r.json())
      .then(d => setProducts(d))
      .catch(() => { })

    // Fetch suppliers for dropdown
    fetch('/api/inventory/suppliers/', { credentials: 'include' })
      .then(r => r.json())
      .then(d => setSuppliers(d))
      .catch(() => { })
  }, [])

  const handleSubmit = async () => {
    if (!form.product || !form.supplier || !form.qty || Number(form.qty) <= 0) return
    setIsSubmitting(true)

    const payload = {
      product: Number(form.product),
      movement_type: 'INBOUND',
      quantity: Number(form.qty),
      supplier: Number(form.supplier),
      expected_date: form.expected_date ? form.expected_date : null,
      notes: form.notes
    }

    try {
      const resp = await fetch('/api/inventory/stock-movements/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (resp.ok) {
        setSubmitted(true)
        setShowForm(false)
        fetchDeliveries() // Refresh table
      }
    } catch {
      // handle error
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto animate-[fadeIn_0.5s_ease-out] pb-12">

      {/* Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/40">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center">
            <FiTruck size={24} />
          </div>
          <div>
            <h1 className="text-[1.18rem] font-semibold text-gray-900 tracking-tight">Receive Stock</h1>
            <p className="text-sm font-medium text-gray-500">Log incoming shipments and update the warehouse ledger.</p>
          </div>
        </div>
        <button
          onClick={() => { setShowForm(!showForm); setSubmitted(false); }}
          className="px-6 py-3 bg-gray-900 text-white rounded-xl text-sm font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-2"
        >
          <FiArrowDown className={`transition-transform duration-300 ${showForm ? 'rotate-180' : ''}`} />
          {showForm ? 'Cancel Entry' : 'Log New Delivery'}
        </button>
      </div>

      {/* Slide-down Form */}
      {showForm && !submitted && (
        <div className="bg-white rounded-3xl border border-emerald-100 shadow-2xl shadow-emerald-100/50 p-8 animate-[slideDown_0.3s_ease-out]">
          <div className="flex items-center gap-2 text-emerald-600 mb-6 border-b border-gray-50 pb-4">
            <FiPackage />
            <h4 className="font-semibold text-gray-900 tracking-tight">New Delivery Entry</h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-widest pl-1">Product *</label>
              <select value={form.product} onChange={(e) => setForm({ ...form, product: e.target.value })} className="w-full px-4 py-3 border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-emerald-500 rounded-xl text-sm font-bold text-gray-700 transition-all">
                <option value="">Select product...</option>
                {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-widest pl-1">Supplier *</label>
              <select value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })} className="w-full px-4 py-3 border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-emerald-500 rounded-xl text-sm font-bold text-gray-700 transition-all">
                <option value="">Select supplier...</option>
                {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-widest pl-1">Quantity *</label>
              <input type="number" value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })}
                placeholder="0" className="w-full px-4 py-3 border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-emerald-500 rounded-xl text-sm font-black text-gray-900 transition-all" />
            </div>
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-widest pl-1">Expected Date</label>
              <input type="date" value={form.expected_date} onChange={(e) => setForm({ ...form, expected_date: e.target.value })}
                className="w-full px-4 py-3 border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-emerald-500 rounded-xl text-sm font-bold text-gray-700 transition-all" />
            </div>
          </div>

          <div className="space-y-2 mt-6">
            <label className="text-[11px] font-bold text-gray-400 uppercase tracking-widest pl-1">Inspection Notes</label>
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Any damages, missing items, or inspection notes..."
              className="w-full px-4 py-3 border-none bg-gray-50 focus:bg-white focus:ring-2 focus:ring-emerald-500 rounded-xl text-sm font-medium text-gray-700 transition-all resize-none" rows={2} />
          </div>

          <div className="flex gap-4 mt-8 pt-6 border-t border-gray-50">
            <button
              disabled={!form.product || !form.supplier || !form.qty || Number(form.qty) <= 0 || isSubmitting}
              onClick={handleSubmit}
              className="px-8 py-3 bg-emerald-500 text-white font-bold rounded-xl hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Logging...' : 'Confirm Receipt'}
            </button>
            <button onClick={() => setShowForm(false)} className="px-6 py-3 font-bold text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Success Banner */}
      {submitted && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-3xl p-6 flex items-center justify-between shadow-lg shadow-emerald-100/50 animate-[slideDown_0.3s_ease-out]">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-emerald-500 shadow-sm shrink-0">
              <FiCheckCircle size={24} />
            </div>
            <div>
              <p className="text-lg font-bold text-emerald-900">Delivery Logged Successfully</p>
              <p className="text-sm font-medium text-emerald-700 mt-0.5">Inventory master count has been updated with <span className="font-black">+{form.qty} units</span>.</p>
            </div>
          </div>
          <button onClick={() => { setShowForm(false); setSubmitted(false); setForm({ product: '', supplier: '', qty: '', expected_date: '', notes: '' }); }}
            className="px-4 py-2 font-bold text-emerald-600 hover:bg-emerald-100 rounded-xl transition-colors text-sm">
            Dismiss
          </button>
        </div>
      )}

      {/* Recent Deliveries Table */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/40 relative overflow-hidden">

        <div className="px-8 py-6 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
          <div className="flex items-center gap-2 text-gray-900">
            <FiCalendar className="text-gray-400" />
            <h4 className="font-semibold text-[1rem] tracking-tight">Recent Deliveries</h4>
          </div>
          <div className="bg-white border border-gray-200 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <FiSearch className="text-gray-400" />
            <input 
              type="text" 
              placeholder="Search PO or Product..." 
              value={search} 
              onChange={(e) => setSearch(e.target.value)} 
              className="border-none bg-transparent outline-none text-xs font-bold w-48 focus:ring-0 text-gray-700" 
            />
          </div>
        </div>

        {loadingDeliveries ? (
          <div className="p-12 text-center text-gray-400 font-bold uppercase tracking-widest text-sm animate-pulse">
            Loading recent ledger...
          </div>
        ) : recentDeliveries.length === 0 ? (
          <div className="p-12 text-center">
            <FiPackage size={48} className="mx-auto text-gray-200 mb-4" />
            <h3 className="text-xl font-black text-gray-400">No recent deliveries</h3>
          </div>
        ) : (
          <div className="overflow-x-auto min-h-[300px]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white border-b border-gray-100">
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest">Delivery ID</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest">Product</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest">Supplier</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest text-right">Qty</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest">Expected</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest">Notes</th>
                  <th className="px-8 py-5 text-[11px] font-bold text-gray-400 uppercase tracking-widest">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {recentDeliveries.filter(d => {
                  if (!search) return true;
                  const searchLower = search.toLowerCase();
                  const prodName = d.product_name || (d.product_obj && d.product_obj.name) || 'Unknown';
                  const idStr = `inb-${d.id.toString().padStart(4, '0')}`;
                  
                  return prodName.toLowerCase().includes(searchLower) || idStr.includes(searchLower);
                }).slice(0, 10).map((d) => {
                  const prodName = d.product_name || (d.product_obj && d.product_obj.name) || 'Unknown'
                  const supplier = d.supplier_name || (d.supplier_obj && d.supplier_obj.name) || 'Internal'
                  const dateObj = d.expected_date ? new Date(d.expected_date) : null

                  return (
                    <tr key={d.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-8 py-4">
                        <span className="text-[12px] font-mono font-bold text-gray-400">INB-{d.id.toString().padStart(4, '0')}</span>
                      </td>
                      <td className="px-8 py-4">
                        <span className="font-bold text-gray-900 text-sm block">{prodName}</span>
                        <span className="text-[10px] text-gray-400 font-mono">{(d.product_obj?.sku) || d.product_sku}</span>
                      </td>
                      <td className="px-8 py-4">
                        <span className="text-[13px] font-medium text-gray-600">{supplier}</span>
                      </td>
                      <td className="px-8 py-4 text-right">
                        <span className="text-[1rem] font-semibold text-emerald-600">+{d.quantity}</span>
                      </td>
                      <td className="px-8 py-4">
                        <span className="text-[13px] font-bold text-gray-900">{dateObj ? dateObj.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : '-'}</span>
                      </td>
                      <td className="px-8 py-4">
                        <span className="text-[12px] font-medium text-gray-500 max-w-[150px] truncate block" title={d.notes || ''}>{d.notes || '-'}</span>
                      </td>
                      <td className="px-8 py-4">
                        <span className="inline-flex px-3 py-1 rounded-full text-[10px] bg-emerald-50 text-emerald-700 font-black tracking-widest uppercase border border-emerald-100">
                          Completed
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
        <div className="p-4 border-t border-gray-100 bg-gray-50/50 text-center">
          <button className="text-sm font-bold text-indigo-600 hover:text-indigo-800 transition-colors">
            View Full Auditing Ledger &rarr;
          </button>
        </div>
      </div>
    </div>
  );
}
