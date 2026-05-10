import { useEffect, useState } from 'react'

type InvoiceRow = {
  id: number
  invoice_number: string
  order: number
  order_number: string
  customer_name: string
  amount_ron: string
  status: string
  effective_status: string
  issued_date: string
  due_date: string | null
}

type InvoiceListResponse = {
  count: number
  next: string | null
  previous: string | null
  results: InvoiceRow[]
  paid_total: string
  pending_total: string
  overdue_total: string
}

type StatusFilter = '' | 'PAID' | 'ISSUED' | 'OVERDUE'

const STATUS_TABS: { label: string; value: StatusFilter }[] = [
  { label: 'All', value: '' },
  { label: 'Paid', value: 'PAID' },
  { label: 'Pending', value: 'ISSUED' },
  { label: 'Overdue', value: 'OVERDUE' },
]

const effectiveStatusBadge = (status: string) => {
  const s = status.toUpperCase()
  if (s === 'OVERDUE') {
    return (
      <span className="inline-flex rounded-full px-2 py-1 text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
        Overdue
      </span>
    )
  }
  if (s === 'PAID') {
    return (
      <span className="inline-flex rounded-full px-2 py-1 text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
        Paid
      </span>
    )
  }
  if (s === 'DRAFT') {
    return (
      <span className="inline-flex rounded-full px-2 py-1 text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
        Draft
      </span>
    )
  }
  return (
    <span className="inline-flex rounded-full px-2 py-1 text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
      Pending
    </span>
  )
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

const formatDate = (value: string | null) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('ro-RO')
}

const SalesInvoicesPage = () => {
  const [invoices, setInvoices] = useState<InvoiceRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [statusFilter, setStatusFilter] = useState<StatusFilter>('')
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [nextPageUrl, setNextPageUrl] = useState<string | null>(null)
  const [previousPageUrl, setPreviousPageUrl] = useState<string | null>(null)

  const [paidTotal, setPaidTotal] = useState('0.00')
  const [pendingTotal, setPendingTotal] = useState('0.00')
  const [overdueTotal, setOverdueTotal] = useState('0.00')

  useEffect(() => {
    setPage(1)
  }, [statusFilter])

  useEffect(() => {
    const loadInvoices = async () => {
      try {
        setLoading(true)
        setError('')

        const params = new URLSearchParams()
        params.set('page', String(page))
        params.set('page_size', '20')
        if (statusFilter) params.set('status', statusFilter)

        const response = await fetch(`/api/invoices/?${params.toString()}`, {
          credentials: 'include',
        })

        if (!response.ok) throw new Error(`Request failed with status ${response.status}`)

        const data = (await response.json()) as InvoiceListResponse
        setInvoices(Array.isArray(data.results) ? data.results : [])
        setTotalCount(data.count ?? 0)
        setNextPageUrl(data.next ?? null)
        setPreviousPageUrl(data.previous ?? null)
        setPaidTotal(data.paid_total ?? '0.00')
        setPendingTotal(data.pending_total ?? '0.00')
        setOverdueTotal(data.overdue_total ?? '0.00')
      } catch (err) {
        console.error('Failed to load invoices:', err)
        setError('Could not load invoices right now.')
      } finally {
        setLoading(false)
      }
    }

    loadInvoices()
  }, [statusFilter, page])

  return (
    <div className="space-y-6">
      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Invoices</h2>
            <p className="text-sm text-black/60 mt-1">Track billing status across all sales orders.</p>
          </div>
          <div className="text-right text-sm text-black/60">
            <p>{totalCount} invoices</p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
          <p className="text-xs uppercase tracking-wide text-black/50 font-semibold">Paid</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrencyRon(paidTotal)}</p>
        </section>
        <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
          <p className="text-xs uppercase tracking-wide text-black/50 font-semibold">Pending</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{formatCurrencyRon(pendingTotal)}</p>
        </section>
        <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
          <p className="text-xs uppercase tracking-wide text-black/50 font-semibold">Overdue</p>
          <p className="text-2xl font-bold text-rose-600 mt-1">{formatCurrencyRon(overdueTotal)}</p>
        </section>
      </div>

      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5 space-y-4">
        <div className="flex gap-2">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setStatusFilter(tab.value)}
              className={`rounded-lg px-3 py-1.5 text-sm border transition-colors ${
                statusFilter === tab.value
                  ? 'bg-black text-white border-black'
                  : 'bg-white text-black/70 border-[var(--border)] hover:bg-black/[0.04]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <p className="text-sm text-black/60">Loading invoices...</p>
        ) : error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : invoices.length === 0 ? (
          <p className="text-sm text-black/60">No invoices found.</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-y-2">
                <thead>
                  <tr>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Invoice</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Order</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Customer</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Issued</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Due</th>
                    <th className="text-left text-xs uppercase tracking-wide text-black/50 px-3">Status</th>
                    <th className="text-right text-xs uppercase tracking-wide text-black/50 px-3">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((invoice) => (
                    <tr key={invoice.id} className="bg-white border border-[var(--border)]">
                      <td className="px-3 py-2 text-sm font-semibold font-mono">{invoice.invoice_number}</td>
                      <td className="px-3 py-2 text-sm text-black/60 font-mono">{invoice.order_number}</td>
                      <td className="px-3 py-2 text-sm">{invoice.customer_name}</td>
                      <td className="px-3 py-2 text-sm text-black/60">{formatDate(invoice.issued_date)}</td>
                      <td className="px-3 py-2 text-sm text-black/60">{formatDate(invoice.due_date)}</td>
                      <td className="px-3 py-2 text-sm">{effectiveStatusBadge(invoice.effective_status)}</td>
                      <td className="px-3 py-2 text-sm text-right font-semibold">{formatCurrencyRon(invoice.amount_ron)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-black/60">Page {page} · {totalCount} total</p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!previousPageUrl}
                  className="rounded-lg border border-[var(--border)] bg-white px-3 py-1.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
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
    </div>
  )
}

export default SalesInvoicesPage
