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
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-[1.15rem] font-semibold tracking-tight">Invoices</h2>
          <p className="text-[0.875rem] text-[var(--muted-foreground)] mt-0.5">Billing status across all sales orders.</p>
        </div>
        <span className="text-[0.78rem] text-[var(--muted-foreground)] bg-[var(--muted)] px-2.5 py-0.5 rounded-full border border-[var(--border)]">
          {totalCount} total
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.72rem] uppercase tracking-wide text-[var(--muted-foreground)] font-medium">Paid</p>
          <p className="text-[1.6rem] font-bold text-emerald-600 mt-1 leading-none">{formatCurrencyRon(paidTotal)}</p>
        </div>
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.72rem] uppercase tracking-wide text-[var(--muted-foreground)] font-medium">Pending</p>
          <p className="text-[1.6rem] font-bold text-amber-600 mt-1 leading-none">{formatCurrencyRon(pendingTotal)}</p>
        </div>
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.72rem] uppercase tracking-wide text-[var(--muted-foreground)] font-medium">Overdue</p>
          <p className="text-[1.6rem] font-bold text-rose-600 mt-1 leading-none">{formatCurrencyRon(overdueTotal)}</p>
        </div>
      </div>

      <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-[var(--border)] flex items-center gap-2">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setStatusFilter(tab.value)}
              className={`h-7 px-3 text-[0.8rem] rounded-md border transition-colors ${
                statusFilter === tab.value
                  ? 'bg-[var(--primary)] text-white border-[var(--primary)]'
                  : 'bg-transparent text-[var(--muted-foreground)] border-[var(--border)] hover:bg-[var(--muted)]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <p className="px-5 py-8 text-[0.875rem] text-[var(--muted-foreground)]">Loading…</p>
        ) : error ? (
          <p className="px-5 py-8 text-[0.875rem] text-rose-600">{error}</p>
        ) : invoices.length === 0 ? (
          <p className="px-5 py-8 text-[0.875rem] text-[var(--muted-foreground)]">No invoices found.</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-[0.875rem]">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--muted)]/40">
                    <th className="px-5 py-2.5 text-left text-[0.72rem] font-semibold text-[var(--muted-foreground)] uppercase tracking-wide">Invoice</th>
                    <th className="px-5 py-2.5 text-left text-[0.72rem] font-semibold text-[var(--muted-foreground)] uppercase tracking-wide">Order</th>
                    <th className="px-5 py-2.5 text-left text-[0.72rem] font-semibold text-[var(--muted-foreground)] uppercase tracking-wide">Customer</th>
                    <th className="px-5 py-2.5 text-left text-[0.72rem] font-semibold text-[var(--muted-foreground)] uppercase tracking-wide">Issued</th>
                    <th className="px-5 py-2.5 text-left text-[0.72rem] font-semibold text-[var(--muted-foreground)] uppercase tracking-wide">Due</th>
                    <th className="px-5 py-2.5 text-left text-[0.72rem] font-semibold text-[var(--muted-foreground)] uppercase tracking-wide">Status</th>
                    <th className="px-5 py-2.5 text-right text-[0.72rem] font-semibold text-[var(--muted-foreground)] uppercase tracking-wide">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((invoice) => (
                    <tr key={invoice.id} className="border-t border-[var(--border)] hover:bg-[var(--muted)]/40 transition-colors">
                      <td className="px-5 py-3 font-semibold font-mono text-[0.8rem]">{invoice.invoice_number}</td>
                      <td className="px-5 py-3 text-[var(--muted-foreground)] font-mono text-[0.8rem]">{invoice.order_number}</td>
                      <td className="px-5 py-3">{invoice.customer_name}</td>
                      <td className="px-5 py-3 text-[var(--muted-foreground)]">{formatDate(invoice.issued_date)}</td>
                      <td className="px-5 py-3 text-[var(--muted-foreground)]">{formatDate(invoice.due_date)}</td>
                      <td className="px-5 py-3">{effectiveStatusBadge(invoice.effective_status)}</td>
                      <td className="px-5 py-3 text-right font-semibold">{formatCurrencyRon(invoice.amount_ron)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="px-5 py-3 border-t border-[var(--border)] bg-[var(--muted)]/20 flex items-center justify-between">
              <p className="text-[0.78rem] text-[var(--muted-foreground)]">Page {page} · {totalCount} total</p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!previousPageUrl}
                  className="h-8 px-3 text-[0.8rem] rounded-lg border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--muted)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!nextPageUrl}
                  className="h-8 px-3 text-[0.8rem] rounded-lg border border-[var(--border)] bg-[var(--card)] hover:bg-[var(--muted)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default SalesInvoicesPage
