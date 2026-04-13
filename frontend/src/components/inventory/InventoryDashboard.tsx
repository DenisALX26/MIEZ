import { useEffect, useState } from "react";
import { FiX, FiActivity, FiPackage, FiBox, FiAlertTriangle, FiXCircle, FiTruck, FiRepeat } from "react-icons/fi";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Sankey, AreaChart, Area } from "recharts";

// --- API DATA TYPES ---
interface DashboardKpis {
  total_products: number;
  low_stock_count: number;
  out_of_stock_count: number;
  deliveries_today: number;
}

// --- MOCK DATA ---
const products = [
  {
    id: 1, name: "Laptop Stand X2", sku: "SKU-001", category: "Electronics", stock: 45, minStock: 10, status: "OK", supplier: "TechSupply SRL", lastReceived: "01 Mar", history: [
      { day: "1", qty: 50 }, { day: "5", qty: 48 }, { day: "10", qty: 45 }, { day: "15", qty: 42 }, { day: "20", qty: 47 }, { day: "25", qty: 45 },
    ]
  },
  {
    id: 2, name: "USB-C Hub Pro", sku: "SKU-002", category: "Electronics", stock: 6, minStock: 10, status: "Low", supplier: "GadgetWorld SRL", lastReceived: "25 Feb", history: [
      { day: "1", qty: 20 }, { day: "5", qty: 15 }, { day: "10", qty: 12 }, { day: "15", qty: 10 }, { day: "20", qty: 8 }, { day: "25", qty: 6 },
    ]
  },
  {
    id: 3, name: "Office Chair B", sku: "SKU-003", category: "Furniture", stock: 0, minStock: 5, status: "Out", supplier: "FurnitureRO SRL", lastReceived: "10 Feb", history: [
      { day: "1", qty: 8 }, { day: "5", qty: 5 }, { day: "10", qty: 3 }, { day: "15", qty: 2 }, { day: "20", qty: 1 }, { day: "25", qty: 0 },
    ]
  },
  {
    id: 4, name: "Desk Lamp LED", sku: "SKU-004", category: "Lighting", stock: 23, minStock: 8, status: "OK", supplier: "LightHouse SRL", lastReceived: "05 Mar", history: [
      { day: "1", qty: 30 }, { day: "5", qty: 28 }, { day: "10", qty: 25 }, { day: "15", qty: 22 }, { day: "20", qty: 25 }, { day: "25", qty: 23 },
    ]
  },
  {
    id: 5, name: "Wireless Mouse", sku: "SKU-005", category: "Electronics", stock: 32, minStock: 15, status: "OK", supplier: "TechSupply SRL", lastReceived: "03 Mar", history: [
      { day: "1", qty: 40 }, { day: "5", qty: 38 }, { day: "10", qty: 35 }, { day: "15", qty: 33 }, { day: "20", qty: 34 }, { day: "25", qty: 32 },
    ]
  },
];

const depositFlowData = {
  nodes: [
    { name: "TechSupply SRL",  type: "supplier" },
    { name: "GadgetWorld SRL", type: "supplier" },
    { name: "FurnitureRO SRL", type: "supplier" },
    { name: "LightHouse SRL",  type: "supplier" },
    { name: "Wireless Mouse",  type: "product" },
    { name: "Laptop Stand X2", type: "product" },
    { name: "Desk Lamp LED",   type: "product" },
    { name: "Office Chair B",  type: "product" },
    { name: "USB-C Hub Pro",   type: "product" },
    { name: "Main Warehouse",  type: "warehouse" },
    { name: "Sales Orders",    type: "out" },
    { name: "Returns",         type: "out" },
    { name: "Adjustments",     type: "out" },
  ],
  links: [
    // Suppliers to Products
    { source: 0, target: 4, value: 40, items: "Mouse × 40" },
    { source: 0, target: 5, value: 50, items: "Stand × 50" },
    { source: 1, target: 8, value: 20, items: "Hub × 20" },
    { source: 2, target: 7, value: 8,  items: "Chair × 8" },
    { source: 3, target: 6, value: 30, items: "Lamp × 30" },
    // Products to Warehouse
    { source: 4, target: 9, value: 40, items: "Processing..." },
    { source: 5, target: 9, value: 50, items: "Processing..." },
    { source: 6, target: 9, value: 30, items: "Processing..." },
    { source: 7, target: 9, value: 8,  items: "Processing..." },
    { source: 8, target: 9, value: 20, items: "Processing..." },
    // Warehouse to Destinations
    { source: 9, target: 10, value: 120, items: "Shipped Out" },
    { source: 9, target: 11, value: 20,  items: "Returned to Vendor" },
    { source: 9, target: 12, value: 8,   items: "Stock Adjustments" },
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
        <p className="text-[11px] font-bold text-gray-500 uppercase tracking-widest mb-1">{label}</p>
        <p className="text-3xl font-black text-gray-900 tracking-tight">{value}</p>
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
    Low: "bg-amber-50 text-amber-700 border-amber-200",
    Out: "bg-rose-50 text-rose-700 border-rose-200",
  };
  return (
    <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider border ${styles[status] || "bg-gray-50 text-gray-600"}`}>
      {status === 'OK' ? 'Healthy' : status === 'Low' ? 'Low Stock' : 'Depleted'}
    </span>
  );
};

const DetailDrawer = ({ open, onClose, product }: { open: boolean, onClose: () => void, product: any }) => {
  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-40 transition-opacity duration-300 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div className={`fixed inset-y-0 right-0 w-full max-w-md bg-white border-l border-gray-200 z-50 transform transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] flex flex-col ${open ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
          <div>
            <h2 className="text-2xl font-black text-gray-900 tracking-tight">{product?.name}</h2>
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
              {/* Metric Row */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl border border-gray-200 bg-gray-50/50">
                  <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1">Current Stock</p>
                  <p className="text-3xl font-black text-gray-900">{product.stock}</p>
                </div>
                <div className="p-4 rounded-xl border border-gray-200 bg-gray-50/50">
                  <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1">Status</p>
                  <div className="mt-2"><StatusBadge status={product.status} /></div>
                </div>
              </div>

              {/* Info Block */}
              <div className="space-y-3 py-4 border-t border-b border-gray-100">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Minimum Threshold</span>
                  <span className="text-sm font-bold text-gray-900 bg-gray-100 px-2 py-1 rounded">{product.minStock} units</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Supplier</span>
                  <span className="text-sm font-bold text-gray-900">{product.supplier}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 font-medium">Last Received</span>
                  <span className="text-sm font-bold text-gray-900">{product.lastReceived}</span>
                </div>
              </div>

              {/* Recharts Temporal Chart */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <FiActivity className="text-blue-500" />
                  <h3 className="font-bold text-gray-900">30-Day Activity</h3>
                </div>
                <div className="h-48 w-full border border-gray-200 rounded-xl p-4 bg-gray-50/50">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={product.history} margin={{ top: 5, right: 0, left: -25, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorQty" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} dy={10} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: 'none' }}
                      />
                      <Area type="monotone" dataKey="qty" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorQty)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
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
  const [selectedProduct, setSelectedProduct] = useState<typeof products[0] | null>(null);

  useEffect(() => {
    const fetchKpis = async () => {
      try {
        const response = await fetch('/api/inventory/dashboard/', { credentials: 'include' });
        if (response.ok) {
          const data = await response.json();
          setKpis(data);
        }
      } catch (err) {
        console.error('Error fetching inventory KPIs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchKpis();
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
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Intelligence Center</h1>
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
          value={loading ? "..." : (kpis?.total_products || 142)}
          icon={FiBox}
          iconColor="text-blue-600"
        />
        <KPICard
          label="Low Stock Items"
          value={loading ? "..." : (kpis?.low_stock_count || 3)}
          icon={FiAlertTriangle}
          iconColor="text-amber-600"
        />
        <KPICard
          label="Out of Stock"
          value={loading ? "..." : (kpis?.out_of_stock_count || 1)}
          icon={FiXCircle}
          iconColor="text-rose-600"
        />
        <KPICard
          label="Deliveries Expected Today"
          value={loading ? "..." : (kpis?.deliveries_today || 2)}
          icon={FiTruck}
          iconColor="text-emerald-600"
        />
      </div>

      {/* THE ULTIMATE SUPPLY MAP */}
      <div className="w-full">
        <div className="flex items-center justify-between mb-4 px-1">
          <div className="flex items-center gap-2">
            <FiRepeat className="text-gray-400" />
            <h2 className="text-lg font-black text-gray-900 tracking-tight">Global Logistics Map</h2>
          </div>
          <span className="text-[10px] font-bold tracking-widest text-indigo-500 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-200 shadow-sm uppercase shadow-indigo-100">Live End-to-End View</span>
        </div>
        <div className="bg-white rounded-3xl border border-gray-100 shadow-xl shadow-gray-200/50 p-4 sm:p-8">
          <ResponsiveContainer width="100%" height={500}>
            <Sankey
              data={depositFlowData}
              node={(p: any) => <DepositsFlowNode {...p} />}
              link={(p: any) => <DepositsFlowLink {...p} />}
              margin={{ top: 30, right: 100, bottom: 30, left: 100 }}
              nodePadding={24}
              nodeWidth={130}
            />
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
            <h4 className="text-lg font-black text-gray-900 tracking-tight">Active Inventory</h4>
          </div>
        </div>

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
              {products.map((p) => (
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
                    <span className="text-[15px] font-black text-gray-900">{p.stock}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-[14px] text-gray-500 font-semibold">{p.minStock}</span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={p.status} />
                  </td>
                </tr>
              ))}
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