import { useEffect, useMemo, useState } from 'react'

type OrderRow = {
  id: number
  order_number: string
  customer: number
  customer_name: string
  value_ron: string
  date: string
  status: 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'PENDING' | 'RETURNED'
  channel: 'EMAG' | 'WEBSITE' | 'DIRECT'
}

type OrderItemDetail = {
  id: number
  product: number
  product_name: string
  product_sku: string
  quantity: number
  unit_price_ron: string
  line_total_ron: string
}

type OrderDetail = {
  id: number
  order_number: string
  customer: number
  customer_name: string
  created_by: number | null
  created_by_username: string | null
  value_ron: string
  date: string
  status: string
  channel: string
  notes: string
  items: OrderItemDetail[]
}

type OrderListResponse = {
  total_count: number
  total_ron_sum: string
  count: number
  next: string | null
  previous: string | null
  results: OrderRow[]
}

type SalesKpiResponse = {
  orders_today: number
  revenue_today_ron: string
  pending_orders: number
  returns_this_week: number
  pct_changes: {
    orders: number
    revenue: number
  }
}

type DailyOrdersPoint = {
  date: string
  orders_count: number
}

type DailyOrdersResponse = {
  days: DailyOrdersPoint[]
}

type TopProduct = {
  product_id: number
  product_name: string
  product_sku: string
  units_sold: number
}

type TopProductsResponse = {
  week_start: string
  week_end: string
  products: TopProduct[]
}

const statusOptions: Array<{ label: string; value: string }> = [
  { label: 'All statuses', value: '' },
  { label: 'Processing', value: 'PROCESSING' },
  { label: 'Shipped', value: 'SHIPPED' },
  { label: 'Delivered', value: 'DELIVERED' },
  { label: 'Pending', value: 'PENDING' },
  { label: 'Returned', value: 'RETURNED' },
]

const channelOptions: Array<{ label: string; value: string }> = [
  { label: 'All channels', value: '' },
  { label: 'eMAG', value: 'EMAG' },
  { label: 'Website', value: 'WEBSITE' },
  { label: 'Direct', value: 'DIRECT' },
]

const statusBadgeClass: Record<string, string> = {
  PROCESSING: 'bg-blue-50 text-blue-800 border border-blue-200',
  SHIPPED: 'bg-indigo-50 text-indigo-800 border border-indigo-200',
  DELIVERED: 'bg-emerald-50 text-emerald-800 border border-emerald-200',
  PENDING: 'bg-amber-50 text-amber-800 border border-amber-200',
  RETURNED: 'bg-rose-50 text-rose-800 border border-rose-200',
}

const channelBadgeClass: Record<string, string> = {
  EMAG: 'bg-fuchsia-50 text-fuchsia-800 border border-fuchsia-200',
  WEBSITE: 'bg-cyan-50 text-cyan-800 border border-cyan-200',
  DIRECT: 'bg-slate-100 text-slate-700 border border-slate-300',
}

const formatCurrencyRon = (value: string | number) => {
  const numeric = Number(value || 0)
  return new Intl.NumberFormat('ro-RO', {
    style: 'currency',
    currency: 'RON',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numeric)
}

const formatDate = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString('ro-RO')
}

const formatShortDay = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleDateString('ro-RO', { weekday: 'short' })
}

const SalesDashboard = () => {
  const [kpis, setKpis] = useState<SalesKpiResponse | null>(null)
  const [loadingKpis, setLoadingKpis] = useState(true)
  const [kpisError, setKpisError] = useState('')

  const [dailyOrders, setDailyOrders] = useState<DailyOrdersPoint[]>([])
  const [topProducts, setTopProducts] = useState<TopProduct[]>([])
  const [analyticsWeek, setAnalyticsWeek] = useState<{ week_start: string; week_end: string } | null>(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState(true)
  const [analyticsError, setAnalyticsError] = useState('')

  const [orders, setOrders] = useState<OrderRow[]>([])
  const [loadingOrders, setLoadingOrders] = useState(true)
  const [ordersError, setOrdersError] = useState('')

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [channelFilter, setChannelFilter] = useState('')

  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [totalRonSum, setTotalRonSum] = useState('0')
  const [nextPageUrl, setNextPageUrl] = useState<string | null>(null)
  const [previousPageUrl, setPreviousPageUrl] = useState<string | null>(null)

  const [selectedOrder, setSelectedOrder] = useState<OrderDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [detailError, setDetailError] = useState('')

  useEffect(() => {
    setPage(1)
  }, [search, statusFilter, channelFilter])

  useEffect(() => {
    const loadKpis = async () => {
      try {
        setLoadingKpis(true)
        setKpisError('')

        const response = await fetch('/api/sales/dashboard/', {
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error(`Sales KPI request failed with status ${response.status}`)
        }

        const data = (await response.json()) as SalesKpiResponse
        setKpis(data)
      } catch (error) {
        console.error('Failed to load sales KPIs:', error)
        setKpisError('Could not load KPI cards right now.')
      } finally {
        setLoadingKpis(false)
      }
    }

    loadKpis()
  }, [])

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoadingAnalytics(true)
        setAnalyticsError('')

        const [dailyResult, topProductsResult] = await Promise.allSettled([
          fetch('/api/sales/daily-orders/', { credentials: 'include' }),
          fetch('/api/sales/top-products/', { credentials: 'include' }),
        ])

        let dailyLoaded = false

        if (dailyResult.status === 'fulfilled' && dailyResult.value.ok) {
          const dailyData = (await dailyResult.value.json()) as DailyOrdersResponse
          const normalizedDays = Array.isArray(dailyData.days) ? [...dailyData.days] : []
          normalizedDays.sort((a, b) => a.date.localeCompare(b.date))
          setDailyOrders(normalizedDays)
          dailyLoaded = true
        } else {
          setDailyOrders([])
        }

        if (topProductsResult.status === 'fulfilled' && topProductsResult.value.ok) {
          const topData = (await topProductsResult.value.json()) as TopProductsResponse
          setTopProducts(Array.isArray(topData.products) ? topData.products : [])
          setAnalyticsWeek({ week_start: topData.week_start, week_end: topData.week_end })
        } else {
          setTopProducts([])
          setAnalyticsWeek(null)
        }

        if (!dailyLoaded) {
          throw new Error('Daily trend data could not be loaded.')
        }
      } catch (error) {
        console.error('Failed to load sales analytics:', error)
        setAnalyticsError('Could not load weekly sales analytics right now.')
      } finally {
        setLoadingAnalytics(false)
      }
    }

    loadAnalytics()
  }, [])

  useEffect(() => {
    const loadOrders = async () => {
      try {
        setLoadingOrders(true)
        setOrdersError('')

        const params = new URLSearchParams()
        params.set('page', String(page))
        params.set('page_size', '10')

        if (search.trim()) {
          params.set('search', search.trim())
        }
        if (statusFilter) {
          params.set('status', statusFilter)
        }
        if (channelFilter) {
          params.set('channel', channelFilter)
        }

        const response = await fetch(`/api/orders/?${params.toString()}`, {
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error(`Orders request failed with status ${response.status}`)
        }

        const data = (await response.json()) as OrderListResponse
        setOrders(Array.isArray(data.results) ? data.results : [])
        setTotalCount(data.total_count ?? 0)
        setTotalRonSum(data.total_ron_sum ?? '0')
        setNextPageUrl(data.next ?? null)
        setPreviousPageUrl(data.previous ?? null)
      } catch (error) {
        console.error('Failed to load orders list:', error)
        setOrdersError('Could not load orders right now.')
      } finally {
        setLoadingOrders(false)
      }
    }

    loadOrders()
  }, [search, statusFilter, channelFilter, page])

  const openOrderDetail = async (orderId: number) => {
    try {
      setLoadingDetail(true)
      setDetailError('')
      setSelectedOrder(null)

      const response = await fetch(`/api/orders/${orderId}/`, {
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`Order detail request failed with status ${response.status}`)
      }

      const detail = (await response.json()) as OrderDetail
      setSelectedOrder(detail)
    } catch (error) {
      console.error('Failed to load order detail:', error)
      setDetailError('Could not load order details.')
    } finally {
      setLoadingDetail(false)
    }
  }

  const closeModal = () => {
    setSelectedOrder(null)
    setDetailError('')
  }

  const maxDailyOrders = useMemo(() => {
    if (!dailyOrders.length) {
      return 1
    }
    return Math.max(...dailyOrders.map((entry) => entry.orders_count), 1)
  }, [dailyOrders])

  const averageOrderValue = useMemo(() => {
    if (!totalCount) {
      return 0
    }
    return Number(totalRonSum) / totalCount
  }, [totalCount, totalRonSum])

  return (
    <div className="space-y-6">
      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
        <h2 className="text-lg font-semibold">Sales Dashboard</h2>
        <p className="text-sm text-black/60 mt-1">Today KPI snapshot with order operations.</p>

        {loadingKpis ? (
          <p className="text-sm text-black/60 mt-3">Loading KPI cards...</p>
        ) : kpisError ? (
          <p className="text-sm text-red-600 mt-3">{kpisError}</p>
        ) : kpis ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mt-4">
            <div className="rounded-xl border border-[var(--border)] bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-black/50">Orders Today</p>
              <p className="text-2xl font-semibold mt-1">{kpis.orders_today}</p>
              <p className="text-xs mt-1 text-black/60">{kpis.pct_changes.orders}% vs yesterday</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-black/50">Revenue Today</p>
              <p className="text-2xl font-semibold mt-1">{formatCurrencyRon(kpis.revenue_today_ron)}</p>
              <p className="text-xs mt-1 text-black/60">{kpis.pct_changes.revenue}% vs yesterday</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-black/50">Pending Orders</p>
              <p className="text-2xl font-semibold mt-1">{kpis.pending_orders}</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-black/50">Returns This Week</p>
              <p className="text-2xl font-semibold mt-1">{kpis.returns_this_week}</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-black/50">Orders In View</p>
              <p className="text-2xl font-semibold mt-1">{totalCount}</p>
            </div>
          </div>
        ) : null}

      </section>

      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold">Weekly Orders Trend</h3>
            <p className="text-sm text-black/60 mt-1">Last 7 days and top products for current ISO week.</p>
          </div>
          {analyticsWeek && (
            <p className="text-xs text-black/60">
              Week: {formatDate(analyticsWeek.week_start)} - {formatDate(analyticsWeek.week_end)}
            </p>
          )}
        </div>

        {loadingAnalytics ? (
          <p className="text-sm text-black/60 mt-3">Loading chart data...</p>
        ) : analyticsError ? (
          <p className="text-sm text-red-600 mt-3">{analyticsError}</p>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 mt-4">
            <div className="xl:col-span-2 rounded-xl border border-[var(--border)] bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-black/50 mb-3">Orders per day</p>
              <div className="h-52 grid grid-cols-7 gap-2 items-end">
                {dailyOrders.map((point) => {
                  const height = (point.orders_count / maxDailyOrders) * 100
                  return (
                    <div key={point.date} className="h-full flex flex-col justify-end items-center">
                      <span className="text-[11px] text-black/60 mb-1">{point.orders_count}</span>
                      <div className="h-36 w-full flex items-end justify-center">
                        <div
                          className="w-full max-w-12 rounded-t-md bg-cyan-500/80 border border-cyan-600/20"
                          style={{ height: `${Math.max(height, 4)}%` }}
                        />
                      </div>
                      <span className="text-[11px] text-black/60 mt-1">{formatShortDay(point.date)}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-white p-4">
              <p className="text-xs uppercase tracking-wide text-black/50 mb-3">Top products this week</p>
              {topProducts.length === 0 ? (
                <p className="text-sm text-black/60">No product sales this week yet.</p>
              ) : (
                <ul className="space-y-2">
                  {topProducts.map((item, index) => (
                    <li key={item.product_id} className="rounded-lg border border-[var(--border)] px-3 py-2 flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold">
                          {index + 1}. {item.product_name}
                        </p>
                        <p className="text-xs text-black/60">{item.product_sku}</p>
                      </div>
                      <span className="text-sm font-semibold">{item.units_sold} units</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </section>

      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="rounded-xl border border-[var(--border)] bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-black/50">Filtered Orders</p>
            <p className="text-2xl font-semibold mt-1">{totalCount}</p>
          </div>
          <div className="rounded-xl border border-[var(--border)] bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-black/50">Filtered Total Value</p>
            <p className="text-2xl font-semibold mt-1">{formatCurrencyRon(totalRonSum)}</p>
          </div>
          <div className="rounded-xl border border-[var(--border)] bg-white p-4">
            <p className="text-xs uppercase tracking-wide text-black/50">Average Order Value</p>
            <p className="text-2xl font-semibold mt-1">{formatCurrencyRon(averageOrderValue)}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-black/50">Search</label>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Order number or customer name"
              className="w-full mt-1 rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-black/50">Status</label>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="w-full mt-1 rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-sm"
            >
              {statusOptions.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wide text-black/50">Channel</label>
            <select
              value={channelFilter}
              onChange={(event) => setChannelFilter(event.target.value)}
              className="w-full mt-1 rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-sm"
            >
              {channelOptions.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loadingOrders ? (
          <p className="text-sm text-black/60">Loading orders...</p>
        ) : ordersError ? (
          <p className="text-sm text-red-600">{ordersError}</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-y-2">
                <thead>
                  <tr>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Order</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Customer</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Date</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Status</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Channel</th>
                    <th className="text-right text-xs uppercase tracking-wide text-black/50 px-3">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr
                      key={order.id}
                      className="bg-white border border-[var(--border)] cursor-pointer hover:bg-black/[0.02]"
                      onClick={() => openOrderDetail(order.id)}
                    >
                      <td className="px-3 py-2 text-sm font-semibold">{order.order_number}</td>
                      <td className="px-3 py-2 text-sm">{order.customer_name}</td>
                      <td className="px-3 py-2 text-sm">{formatDate(order.date)}</td>
                      <td className="px-3 py-2 text-sm">
                        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${statusBadgeClass[order.status] ?? 'bg-slate-100 text-slate-700 border border-slate-300'}`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-sm">
                        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${channelBadgeClass[order.channel] ?? 'bg-slate-100 text-slate-700 border border-slate-300'}`}>
                          {order.channel}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-sm text-right font-semibold">{formatCurrencyRon(order.value_ron)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-black/60">Page {page}</p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                  disabled={!previousPageUrl}
                  className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((current) => current + 1)}
                  disabled={!nextPageUrl}
                  className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {(loadingDetail || selectedOrder || detailError) && (
        <div className="fixed inset-0 z-50 bg-black/40 p-4 flex items-center justify-center" onClick={closeModal}>
          <div className="w-full max-w-3xl max-h-[85vh] overflow-y-auto bg-white rounded-2xl border border-[var(--border)] p-5" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold">Order Details</h3>
                {selectedOrder && (
                  <p className="text-sm text-black/60 mt-1">
                    {selectedOrder.order_number} · {selectedOrder.customer_name}
                  </p>
                )}
              </div>
              <button type="button" className="rounded-lg border border-[var(--border)] px-3 py-1 text-sm" onClick={closeModal}>
                Close
              </button>
            </div>

            {loadingDetail ? (
              <p className="text-sm text-black/60 mt-4">Loading order details...</p>
            ) : detailError ? (
              <p className="text-sm text-red-600 mt-4">{detailError}</p>
            ) : selectedOrder ? (
              <div className="space-y-4 mt-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  <div className="rounded-xl border border-[var(--border)] p-3">
                    <p className="text-xs uppercase tracking-wide text-black/50">Status</p>
                    <p className="text-sm font-semibold mt-1">{selectedOrder.status}</p>
                  </div>
                  <div className="rounded-xl border border-[var(--border)] p-3">
                    <p className="text-xs uppercase tracking-wide text-black/50">Channel</p>
                    <p className="text-sm font-semibold mt-1">{selectedOrder.channel}</p>
                  </div>
                  <div className="rounded-xl border border-[var(--border)] p-3">
                    <p className="text-xs uppercase tracking-wide text-black/50">Date</p>
                    <p className="text-sm font-semibold mt-1">{formatDate(selectedOrder.date)}</p>
                  </div>
                  <div className="rounded-xl border border-[var(--border)] p-3">
                    <p className="text-xs uppercase tracking-wide text-black/50">Total</p>
                    <p className="text-sm font-semibold mt-1">{formatCurrencyRon(selectedOrder.value_ron)}</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold">Line Items</h4>
                  <div className="overflow-x-auto mt-2">
                    <table className="min-w-full border-separate border-spacing-y-2">
                      <thead>
                        <tr>
                          <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Product</th>
                          <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">SKU</th>
                          <th className="text-right text-xs uppercase tracking-wide text-black/50 px-3">Qty</th>
                          <th className="text-right text-xs uppercase tracking-wide text-black/50 px-3">Unit Price</th>
                          <th className="text-right text-xs uppercase tracking-wide text-black/50 px-3">Line Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedOrder.items.map((item) => (
                          <tr key={item.id} className="bg-white border border-[var(--border)]">
                            <td className="px-3 py-2 text-sm">{item.product_name}</td>
                            <td className="px-3 py-2 text-sm text-black/60">{item.product_sku}</td>
                            <td className="px-3 py-2 text-sm text-right">{item.quantity}</td>
                            <td className="px-3 py-2 text-sm text-right">{formatCurrencyRon(item.unit_price_ron)}</td>
                            <td className="px-3 py-2 text-sm text-right font-semibold">{formatCurrencyRon(item.line_total_ron)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}

export default SalesDashboard