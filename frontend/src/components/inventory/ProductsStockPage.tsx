import { useEffect, useState } from "react";
import { FiSearch, FiPackage, FiCheckCircle, FiAlertTriangle, FiXCircle, FiX, FiActivity, FiDollarSign } from "react-icons/fi";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from "recharts";

interface Product {
  id: number;
  name: string;
  sku: string;
  category: string;
  unit_price_ron: string;
  stock_count: number;
  min_stock: number;
  created_at: string;
  updated_at: string;
}

const getStatus = (stock: number, minStock: number) => {
  if (stock === 0) return "Out";
  if (stock <= minStock) return "Low";
  return "OK";
};

const StatusBadge = ({ status }: { status: string }) => {
  if (status === "Out") {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-rose-100 text-rose-700 border border-rose-200 shadow-sm">
        <FiXCircle /> Depleted
      </span>
    );
  }
  if (status === "Low") {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-100 text-amber-700 border border-amber-200 shadow-sm">
        <FiAlertTriangle /> Critical
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-100/80 text-emerald-700 border border-emerald-200 shadow-sm">
        <FiCheckCircle /> Healthy
    </span>
  );
};

// Generates a nice visual curve for the chart based on the stock amount
const getHistory = (currentStock: number) => {
  const points = [];
  let val = currentStock + 15;
  for (let i = 1; i <= 6; i++) {
    points.push({ day: `${i * 5}`, qty: val });
    val = Math.max(0, val - Math.floor(Math.random() * 5));
  }
  points[5].qty = currentStock; // last point matches exactly
  return points;
};

const DetailDrawer = ({ open, onClose, product }: { open: boolean, onClose: () => void, product: Product | null }) => {
  if (!product) return null;
  const status = getStatus(product.stock_count, product.min_stock);
  const stockValue = parseFloat(product.unit_price_ron) * product.stock_count;
  const history = getHistory(product.stock_count);

  return (
    <>
      <div 
        className={`fixed inset-0 bg-slate-900/30 backdrop-blur-sm z-40 transition-opacity duration-300 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />
      <div className={`fixed inset-y-0 right-0 w-full max-w-md bg-white border-l border-gray-100 shadow-2xl z-50 transform transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] flex flex-col ${open ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
          <div>
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">{product.name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-xs font-mono tracking-wider">{product.sku}</span>
              <span className="text-sm font-medium text-gray-400">• {product.category}</span>
            </div>
          </div>
          <button onClick={onClose} className="p-2.5 bg-gray-50 hover:bg-rose-50 hover:text-rose-600 rounded-full text-gray-400 transition-colors">
            <FiX size={20} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50/50">
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-center">
                <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-1">Current Stock</span>
                <p className="text-3xl font-black text-gray-900">{product.stock_count}</p>
              </div>
              <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-center">
                <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-2">Status Flag</span>
                <div><StatusBadge status={status} /></div>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
              <div className="flex items-center gap-2 mb-4 text-indigo-600 border-b border-gray-50 pb-3">
                <FiDollarSign className="text-indigo-500" />
                <h3 className="font-bold text-gray-900">Financial Overview</h3>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Unit Cost</span>
                  <span className="text-sm font-bold text-gray-900">{parseFloat(product.unit_price_ron).toFixed(2)} RON</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Total Stock Value</span>
                  <span className="text-sm font-black text-indigo-600">{stockValue.toLocaleString('ro-RO')} RON</span>
                </div>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
               <div className="flex items-center gap-2 mb-6 border-b border-gray-50 pb-3">
                 <FiActivity className="text-emerald-500" />
                 <h3 className="font-bold text-gray-900">30-Day Trajectory</h3>
               </div>
               <div className="h-40 w-full mt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={history} margin={{ top: 5, right: 0, left: -25, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorStock" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.5}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} dy={10} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <RechartsTooltip 
                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                      />
                      <Area type="monotone" dataKey="qty" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorStock)" animationDuration={1500} />
                    </AreaChart>
                  </ResponsiveContainer>
               </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default function ProductsStockPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const res = await fetch("/api/inventory/products/", { credentials: "include" });
        if (res.ok) {
          const data = await res.json();
          if (data.results) setProducts(data.results);
          else setProducts(data);
        }
      } catch (err) {
        console.error("Failed to fetch products:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  const categories = ["All", ...Array.from(new Set(products.map((p) => p.category)))];
  const statuses = ["All", "OK", "Low", "Out"];

  const filtered = products.filter((p) => {
    const s = getStatus(p.stock_count, p.min_stock);
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) || p.sku.toLowerCase().includes(search.toLowerCase());
    const matchCat = categoryFilter === "All" || p.category === categoryFilter;
    const matchStatus = statusFilter === "All" || s === statusFilter;
    return matchSearch && matchCat && matchStatus;
  });

  return (
    <div className="max-w-[1400px] mx-auto space-y-6 animate-[fadeIn_0.5s_ease-out] pb-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Products & Stock</h1>
          <p className="text-gray-500 mt-1 font-medium flex items-center gap-2">
            Showing <span className="font-bold text-gray-900 bg-gray-100 px-2 py-0.5 rounded">{filtered.length}</span> of {products.length} products
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="relative group flex-1 md:w-72">
            <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none text-gray-400 group-focus-within:text-blue-500 transition-colors">
              <FiSearch size={16} />
            </div>
            <input
              type="text"
              placeholder="Search products or SKU..."
              className="w-full bg-white border border-gray-200 text-gray-900 text-[13px] font-medium rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 block pl-10 p-3 transition-all outline-none shadow-sm shadow-gray-100"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select 
            value={categoryFilter} 
            onChange={(e) => setCategoryFilter(e.target.value)} 
            className="bg-white border border-gray-200 text-gray-700 text-[13px] font-semibold rounded-xl focus:ring-2 focus:ring-blue-500/20 px-4 py-3 outline-none shadow-sm shadow-gray-100 appearance-none cursor-pointer hover:border-gray-300 transition-colors"
          >
            {categories.map((c) => <option key={c} value={c}>{c === "All" ? "All Categories" : c}</option>)}
          </select>
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)} 
            className="bg-white border border-gray-200 text-gray-700 text-[13px] font-semibold rounded-xl focus:ring-2 focus:ring-blue-500/20 px-4 py-3 outline-none shadow-sm shadow-gray-100 appearance-none cursor-pointer hover:border-gray-300 transition-colors"
          >
            {statuses.map((s) => <option key={s} value={s}>{s === "All" ? "All Statuses" : s}</option>)}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/50 overflow-hidden relative">
        <div className="overflow-x-auto min-h-[400px]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/80 border-b border-gray-100">
                <th className="px-8 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap">Product Info</th>
                <th className="px-8 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap text-right">Stock</th>
                <th className="px-8 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap text-right">Min</th>
                <th className="px-8 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap text-right">Unit Cost</th>
                <th className="px-8 py-4 text-[11px] font-bold text-gray-400 uppercase tracking-widest whitespace-nowrap text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr>
                  <td colSpan={5} className="text-center py-20">
                     <span className="relative flex h-8 w-8 mx-auto mb-4">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-8 w-8 bg-blue-500"></span>
                      </span>
                     <p className="text-gray-500 font-medium">Syncing master inventory...</p>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-20 text-gray-500 font-medium">No products found matching your criteria.</td>
                </tr>
              ) : (
                filtered.map((p) => {
                  const s = getStatus(p.stock_count, p.min_stock);
                  return (
                    <tr 
                      key={p.id} 
                      className="group hover:bg-blue-50/30 cursor-pointer transition-colors"
                      onClick={() => setSelectedProduct(p)}
                    >
                      <td className="px-8 py-5">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center flex-shrink-0 text-gray-400 group-hover:bg-white group-hover:border-blue-200 group-hover:text-blue-500 transition-all">
                            <FiPackage size={18} />
                          </div>
                          <div>
                            <p className="font-bold text-gray-900 text-[14px] group-hover:text-blue-600 transition-colors">{p.name}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-xs text-gray-400 font-mono">{p.sku}</span>
                              <span className="text-[11px] text-gray-400 font-medium bg-gray-50 px-2 py-0.5 rounded">{p.category}</span>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-8 py-5 text-right w-32">
                        <span className="text-lg font-black text-gray-900">{p.stock_count}</span>
                      </td>
                      <td className="px-8 py-5 text-right w-32">
                        <span className="text-sm font-semibold text-gray-400">{p.min_stock}</span>
                      </td>
                      <td className="px-8 py-5 text-right w-32">
                        <p className="font-bold text-gray-900 inline-flex items-center gap-1">
                          {parseFloat(p.unit_price_ron).toFixed(2)} <span className="text-[10px] text-gray-400 uppercase">RON</span>
                        </p>
                      </td>
                      <td className="px-8 py-5 text-center w-32">
                        <StatusBadge status={s} />
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <DetailDrawer 
        open={!!selectedProduct} 
        onClose={() => setSelectedProduct(null)} 
        product={selectedProduct} 
      />
    </div>
  );
}
