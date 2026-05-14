import { useEffect, useState } from "react";
import { FiX, FiPackage, FiBox, FiAlertTriangle, FiXCircle, FiTruck, FiRepeat, FiCheck, FiSearch, FiFilter } from "react-icons/fi";
import { ResponsiveContainer, Sankey } from "recharts";

// --- API DATA TYPES ---
interface DashboardKpis {
  total_products: number;
  low_stock_count: number;
  out_of_stock_count: number;
  deliveries_today: number;
}

interface ApiProduct {
  id: number;
  name: string;
  sku: string;
  category: string;
  stock_count: number;
  min_stock: number;
  unit_price_ron: number;
  status: 'OK' | 'LOW' | 'OUT';
  shortfall: number;
}

interface FlowData {
  nodes: { name: string; type?: string }[];
  links: { source: number; target: number; value: number; items: string }[];
  date_range?: { start: string; end: string };
}

const depositFlowData = {
  nodes: [
    { name: "TechSupply SRL", type: "supplier" },
    { name: "GadgetWorld SRL", type: "supplier" },
    { name: "FurnitureRO SRL", type: "supplier" },
    { name: "LightHouse SRL", type: "supplier" },
    { name: "Wireless Mouse", type: "product" },
    { name: "Laptop Stand X2", type: "product" },
    { name: "Desk Lamp LED", type: "product" },
    { name: "Office Chair B", type: "product" },
    { name: "USB-C Hub Pro", type: "product" },
    { name: "Main Warehouse", type: "warehouse" },
    { name: "Sales Orders", type: "out" },
    { name: "Returns", type: "out" },
    { name: "Adjustments", type: "out" },
  ],
  links: [
    // Suppliers to Products
    { source: 0, target: 4, value: 40, items: "Mouse × 40" },
    { source: 0, target: 5, value: 50, items: "Stand × 50" },
    { source: 1, target: 8, value: 20, items: "Hub × 20" },
    { source: 2, target: 7, value: 8, items: "Chair × 8" },
    { source: 3, target: 6, value: 30, items: "Lamp × 30" },
    // Products to Warehouse
    { source: 4, target: 9, value: 40, items: "Processing..." },
    { source: 5, target: 9, value: 50, items: "Processing..." },
    { source: 6, target: 9, value: 30, items: "Processing..." },
    { source: 7, target: 9, value: 8, items: "Processing..." },
    { source: 8, target: 9, value: 20, items: "Processing..." },
    // Warehouse to Destinations
    { source: 9, target: 10, value: 120, items: "Shipped Out" },
    { source: 9, target: 11, value: 20, items: "Returned to Vendor" },
    { source: 9, target: 12, value: 8, items: "Stock Adjustments" },
  ],
};

function DepositsFlowNode(props: any) {
  const { x, y, width, height, payload } = props;
  const type = payload?.type;

  const strokeColor = type === "warehouse" ? "#3b82f6" : type === "supplier" ? "#10b981" : type === "product" ? "#8b5cf6" : "#f43f5e";
  const bgColor = type === "warehouse" ? "#eff6ff" : type === "supplier" ? "#ecfdf5" : type === "product" ? "#f5f3ff" : "#fff1f2";

  const visualHeight = Math.max(height, 24);
  const visualY = y - (visualHeight - height) / 2;

  return (
    <g>
      <rect
        x={x} y={visualY}
        width={width} height={visualHeight}
        rx={6}
        fill={bgColor}
        stroke={strokeColor}
        strokeWidth={1.5}
        className="transition-all hover:brightness-95"
      />
      <text
        x={x + width / 2} y={visualY + visualHeight / 2}
        textAnchor="middle" dominantBaseline="middle"
        fontSize={11} fontWeight={700} fill={strokeColor}
      >
        {payload.name}
      </text>
    </g>
  );
}

function DepositsFlowLink(props: any) {
  const { sourceX, sourceY, targetX, targetY, sourceControlX, targetControlX, linkWidth, payload } = props;

  const path = `M${sourceX},${sourceY} C${sourceControlX},${sourceY} ${targetControlX},${targetY} ${targetX},${targetY}`;

  const isOutbound = payload?.source?.type === "warehouse" || payload?.source === 9;
  const isSupplierToProduct = payload?.source?.type === "supplier" || payload?.source < 4;

  const strokeColor = isOutbound ? "#fb7185" : isSupplierToProduct ? "#34d399" : "#a78bfa";

  return (
    <g className="group animate-[fadeIn_0.5s_ease-out]">
      <path
        d={path}
        fill="none"
        stroke="#f8fafc"
        strokeWidth={Math.max(linkWidth, 8)}
      />
      <path
        d={path}
        fill="none"
        stroke={strokeColor}
        strokeWidth={3}
        strokeDasharray="6 8"
        className="animate-flow group-hover:stroke-[4px] transition-all"
      />
      <title>{payload?.items || ''}</title>
    </g>
  );
}

// --- UI COMPONENTS ---
const KPICard = ({ label, value, icon: Icon, iconColor }: any) => (
  <div className="p-5 rounded-xl border border-gray-200 bg-white hover:border-gray-300 transition-colors">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-widest mb-1">{label}</p>
        <p className="text-2xl font-bold text-gray-900 tracking-tight">{value}</p>
      </div>
      <div className={`p-3 rounded-xl bg-gray-50 border border-gray-100 ${iconColor}`}>
        <Icon size={24} strokeWidth={2.5} />
      </div>
    </div>
  </div>
);

const StatusBadge = ({ status }: { status: string }) => {
  const styles: Record<string, string> = {
    OK: "bg-emerald-50 text-emerald-700 border-emerald-200",
    LOW: "bg-amber-50 text-amber-700 border-amber-200",
    OUT: "bg-rose-50 text-rose-700 border-rose-200",
  };
  const label: Record<string, string> = { OK: 'Healthy', LOW: 'Low Stock', OUT: 'Depleted' };
  const icons: Record<string, any> = { OK: FiCheck, LOW: FiAlertTriangle, OUT: FiXCircle };
  const Icon = icons[status] || FiBox;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider border ${styles[status] ?? "bg-gray-50 text-gray-600"}`}>
      <Icon size={12} strokeWidth={3} />
      {label[status] ?? status}
    </span>
  );
};

const DetailDrawer = ({ open, onClose, product }: { open: boolean, onClose: () => void, product: ApiProduct | null }) => {
  return (
    <>
      <div
        className={`fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity duration-300 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />
      <div className={`fixed inset-y-0 right-0 w-full max-w-md bg-white border-l border-gray-200 z-50 transform transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] flex flex-col ${open ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
          <div>
            <h2 className="text-[1.18rem] font-semibold text-gray-900 tracking-tight">{product?.name}</h2>
            <p className="text-sm text-gray-500 flex items-center gap-2 mt-1">
              <span className="bg-gray-100 px-2 py-0.5 rounded text-xs font-mono">{product?.sku}</span>
              • {product?.category}
            </p>
          </div>
          <button onClick={onClose} className="p-2 bg-gray-50 hover:bg-gray-100 rounded-full text-gray-500 transition-colors">
            <FiX size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-white">
          {product && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl border border-gray-200 bg-gray-50/50">
                  <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1">Current Stock</p>
                  <p className="text-2xl font-bold text-gray-900">{product.stock_count}</p>
                </div>
                <div className="p-4 rounded-xl border border-gray-200 bg-gray-50/50">
                  <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1">Status</p>
                  <div className="mt-2"><StatusBadge status={product.status} /></div>
                </div>
              </div>

              <div className="space-y-3 py-4 border-t border-b border-gray-100">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Minimum Threshold</span>
                  <span className="text-sm font-bold text-gray-900 bg-gray-100 px-2 py-1 rounded">{product.min_stock} units</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Unit Price</span>
                  <span className="text-sm font-bold text-gray-900">{(product.unit_price_ron || 0).toFixed(2)} RON</span>
                </div>
                {product.status !== 'OK' && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500 font-medium">Shortfall</span>
                    <span className="text-sm font-bold text-rose-700 bg-rose-50 px-2 py-1 rounded">{product.shortfall} units</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

// --- MAIN DASHBOARD COMPONENT ---
export default function InventoryDashboard() {
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState<ApiProduct[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<ApiProduct | null>(null);
  const [flowData, setFlowData] = useState<FlowData | null>(null);

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [totalProducts, setTotalProducts] = useState(0);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetch('/api/inventory/dashboard/', { credentials: 'include' })
      .then(r => { if (r.ok) return r.json(); throw new Error() })
      .then(data => setKpis(data))
      .catch(() => { })
      .finally(() => setLoading(false))
  }, []);

  useEffect(() => {
    setLoadingProducts(true);
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (category !== 'All') params.append('category', category);
    if (statusFilter !== 'All') params.append('status', statusFilter);
    params.append('page', page.toString());

    fetch(`/api/inventory/products/?${params.toString()}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        if (data && data.results && Array.isArray(data.results)) {
          setProducts(data.results);
          setTotalProducts(data.count ?? 0);
        } else if (Array.isArray(data)) {
          setProducts(data);
          setTotalProducts(data.length);
        } else {
          setProducts([]);
          setTotalProducts(0);
        }
      })
      .catch(() => {
        setProducts([]);
        setTotalProducts(0);
      })
      .finally(() => setLoadingProducts(false))
  }, [search, category, statusFilter, page]);

  useEffect(() => {
    fetch('/api/inventory/flow/?days=7', { credentials: 'include' })
      .then(r => r.json())
      .then(data => setFlowData(data))
      .catch(() => { })
  }, []);

  return (
    <div className="max-w-[1400px] mx-auto space-y-8 pb-10">
      <style>{`
        @keyframes flow {
          to { stroke-dashoffset: -16px; }
        }
        .animate-flow {
          animation: flow 1s linear infinite;
        }
      `}</style>

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-gray-200 pb-6">
        <div>
          <h1 className="text-[1.18rem] font-semibold text-gray-900 tracking-tight">Intelligence Center</h1>
          <p className="text-gray-500 mt-1 font-medium">Real-time inventory metrics and forecasting.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <span className="text-[11px] font-bold text-gray-500 uppercase tracking-widest">Live Sync Active</span>
        </div>
      </div>

      {/* KPI GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          label="Total Products"
          value={loading ? "..." : (kpis?.total_products ?? 0)}
          icon={FiBox}
          iconColor="text-blue-600"
        />
        <KPICard
          label="Low Stock Items"
          value={loading ? "..." : (kpis?.low_stock_count ?? 0)}
          icon={FiAlertTriangle}
          iconColor="text-amber-600"
        />
        <KPICard
          label="Out of Stock"
          value={loading ? "..." : (kpis?.out_of_stock_count ?? 0)}
          icon={FiXCircle}
          iconColor="text-rose-600"
        />
        <KPICard
          label="Deliveries Expected Today"
          value={loading ? "..." : (kpis?.deliveries_today ?? 0)}
          icon={FiTruck}
          iconColor="text-emerald-600"
        />
      </div>

      {/* THE ULTIMATE SUPPLY MAP */}
      <div className="w-full">
        <div className="flex items-center justify-between mb-4 px-1">
          <div className="flex items-center gap-2">
            <FiRepeat className="text-gray-400" />
            <h2 className="text-[1rem] font-semibold text-gray-900 tracking-tight">Stock Movement Flow</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest text-gray-400">
              <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Inbound</div>
              <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-400"></span> Outbound</div>
            </div>
            {flowData?.date_range ? (
              <span className="text-[10px] font-bold tracking-widest text-indigo-500 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-200 shadow-sm uppercase shadow-indigo-100">
                Last 7 Days • {new Date(flowData.date_range.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}–{new Date(flowData.date_range.end).toLocaleDateString('en-US', { day: 'numeric' })}
              </span>
            ) : (
              <span className="text-[10px] font-bold tracking-widest text-indigo-500 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-200 shadow-sm uppercase shadow-indigo-100">Live End-to-End View</span>
            )}
          </div>
        </div>
        <div className="bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/50 p-4 sm:p-8 min-h-[500px]">
          <ResponsiveContainer width="100%" height={500}>
            {flowData && flowData.nodes && flowData.nodes.length > 0 ? (
              <Sankey
                data={flowData}
                node={(p: any) => <DepositsFlowNode {...p} />}
                link={(p: any) => <DepositsFlowLink {...p} />}
                margin={{ top: 30, right: 100, bottom: 30, left: 100 }}
                nodePadding={24}
                nodeWidth={130}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400 font-medium animate-pulse">Loading logistics...</div>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* PRODUCTS TABLE */}
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <div className="px-6 py-5 flex items-center justify-between border-b border-gray-200 bg-gray-50/30">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <FiPackage size={20} />
            </div>
            <h4 className="text-[1rem] font-semibold text-gray-900 tracking-tight">Active Inventory</h4>
          </div>
          <div className="text-[11px] font-bold text-gray-500 uppercase tracking-widest bg-white px-3 py-1.5 rounded-lg border border-gray-200 shadow-sm">
            {totalProducts} SKUs
          </div>
        </div>

        <div className="px-6 py-4 flex flex-col sm:flex-row gap-4 border-b border-gray-200 bg-white">
          <div className="relative flex-1">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by product name or SKU..."
              className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <select
                className="appearance-none bg-gray-50 border border-gray-200 text-gray-700 py-2 pl-4 pr-10 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer"
                value={category}
                onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              >
                <option value="All">All Categories</option>
                <option value="SALES">Sales</option>
                <option value="INVENTORY">Inventory</option>
                <option value="GENERAL">General</option>
                <option value="Electronics">Electronics</option>
                <option value="Furniture">Furniture</option>
                <option value="Lighting">Lighting</option>
                <option value="Accessories">Accessories</option>
              </select>
              <FiFilter className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={14} />
            </div>
            <div className="relative">
              <select
                className="appearance-none bg-gray-50 border border-gray-200 text-gray-700 py-2 pl-4 pr-10 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer"
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              >
                <option value="All">All Statuses</option>
                <option value="OK">Healthy (OK)</option>
                <option value="LOW">Low Stock</option>
                <option value="OUT">Out of Stock</option>
              </select>
              <FiFilter className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={14} />
            </div>
          </div>
        </div>

        {loadingProducts ? (
          <p className="px-6 py-8 text-sm text-gray-400">Loading products…</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-wider">Product ID</th>
                  <th className="text-left px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="text-left px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-wider">Stock</th>
                  <th className="text-left px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-wider">Min Stock</th>
                  <th className="text-left px-6 py-4 text-[11px] font-bold text-gray-500 uppercase tracking-wider">Health</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {products.length === 0 ? (
                   <tr>
                     <td colSpan={5} className="px-6 py-8 text-center text-gray-400 font-medium">
                       No products found matching the criteria.
                     </td>
                   </tr>
                ) : (
                  products.map((p) => (
                    <tr
                      key={p.id}
                      onClick={() => setSelectedProduct(p)}
                      className="group hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4">
                        <p className="font-bold text-gray-900 group-hover:text-blue-600 transition-colors">{p.name}</p>
                        <p className="text-xs text-gray-400 font-mono mt-1">{p.sku}</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2 py-1 rounded bg-gray-100 text-gray-600 text-[11px] font-bold">
                          {p.category}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-[0.95rem] font-semibold text-gray-900">{p.stock_count}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-[14px] text-gray-500 font-semibold">{p.min_stock}</span>
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={p.status} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {!loadingProducts && products.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
            <span className="text-sm text-gray-500 font-medium">
              Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, totalProducts || 0)} of {totalProducts || 0} items
            </span>
            <div className="flex gap-2">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="px-3 py-1.5 text-sm font-medium border border-gray-200 rounded-lg bg-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors shadow-sm text-gray-700"
              >
                Previous
              </button>
              <button 
                disabled={page * 10 >= (totalProducts || 0)}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1.5 text-sm font-medium border border-gray-200 rounded-lg bg-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors shadow-sm text-gray-700"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      <DetailDrawer
        open={!!selectedProduct}
        onClose={() => setSelectedProduct(null)}
        product={selectedProduct}
      />
    </div>
  );
}