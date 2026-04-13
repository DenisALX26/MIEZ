import { useEffect, useState } from 'react'
import { FiBox, FiAlertTriangle, FiXCircle, FiTruck } from 'react-icons/fi'

interface DashboardKpis {
  total_products: number
  low_stock_count: number
  out_of_stock_count: number
  deliveries_today: number
}

const InventoryDashboard = () => {
  const [kpis, setKpis] = useState<DashboardKpis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchKpis = async () => {
      try {
        setLoading(true)
        setError('')
        const response = await fetch('/api/inventory/dashboard/', {
          credentials: 'include',
        })
        if (!response.ok) {
          throw new Error(`Failed to fetch dashboard data: ${response.status}`)
        }
        const data = await response.json()
        setKpis(data)
      } catch (err) {
        console.error('Error fetching inventory KPIs:', err)
        setError('Could not load dashboard statistics.')
      } finally {
        setLoading(false)
      }
    }

    fetchKpis()
  }, [])

  if (loading) {
    return (
      <div className="p-6">
        <p className="text-sm text-black/60">Loading inventory statistics...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    )
  }

  const cards = [
    {
      title: 'Total Products',
      value: kpis?.total_products ?? 0,
      icon: FiBox,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-100',
    },
    {
      title: 'Low Stock Items',
      value: kpis?.low_stock_count ?? 0,
      icon: FiAlertTriangle,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-100',
    },
    {
      title: 'Out of Stock',
      value: kpis?.out_of_stock_count ?? 0,
      icon: FiXCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-100',
    },
    {
      title: 'Deliveries Expected Today',
      value: kpis?.deliveries_today ?? 0,
      icon: FiTruck,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-100',
    },
  ]

  return (
    <div className="space-y-6">
      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-6">
        <div className="mb-6">
          <h2 className="text-xl font-bold">Inventory Overview</h2>
          <p className="text-sm text-black/60 mt-1">Real-time stock status and upcoming deliveries.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map((card, index) => (
            <div
              key={index}
              className={`p-5 rounded-xl border ${card.borderColor} ${card.bgColor} transition-all hover:shadow-sm`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-black/60 uppercase tracking-wider">{card.title}</p>
                  <p className="text-3xl font-bold mt-2 text-black/80">{card.value}</p>
                </div>
                <div className={`p-3 rounded-lg bg-white shadow-sm ${card.color}`}>
                  <card.icon size={24} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default InventoryDashboard