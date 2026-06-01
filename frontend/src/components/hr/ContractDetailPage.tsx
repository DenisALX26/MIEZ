import { useEffect, useMemo, useState } from 'react'
import { FiArrowLeft } from 'react-icons/fi'
import { useNavigate, useParams } from 'react-router-dom'

type ContractStatus = 'ACTIVE' | 'EXPIRING' | 'EXPIRED' | 'PENDING'
type ContractType = 'EMPLOYMENT' | 'CONTRACTOR'

type ContractDetail = {
  id: number
  contract_number: string
  employee: number
  employee_name: string
  department: string | null
  type: ContractType
  start_date: string
  end_date: string | null
  salary_ron: string
  status: ContractStatus
}

const STATUS_LABELS: Record<ContractStatus, string> = {
  ACTIVE: 'Active',
  EXPIRING: 'Expiring Soon',
  EXPIRED: 'Expired',
  PENDING: 'Pending',
}

const STATUS_STYLES: Record<ContractStatus, string> = {
  ACTIVE: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  EXPIRING: 'border-amber-200 bg-amber-50 text-amber-700',
  EXPIRED: 'border-rose-200 bg-rose-50 text-rose-700',
  PENDING: 'border-slate-200 bg-slate-50 text-slate-700',
}

const TYPE_LABELS: Record<ContractType, string> = {
  EMPLOYMENT: 'Employment',
  CONTRACTOR: 'Contractor',
}

const formatDate = (value: string | null) => {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export default function ContractDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [contract, setContract] = useState<ContractDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadContract = async () => {
      if (!id) {
        setError('Missing contract id.')
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError('')

        const response = await fetch(`/api/contracts/${id}/`, {
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error(`Failed to load contract detail: ${response.status}`)
        }

        const data = (await response.json()) as ContractDetail
        setContract(data)
      } catch (fetchError) {
        console.error('Failed to load contract detail', fetchError)
        setError('Could not load contract details right now.')
      } finally {
        setLoading(false)
      }
    }

    loadContract()
  }, [id])

  const statusClass = useMemo(() => {
    if (!contract) {
      return STATUS_STYLES.PENDING
    }

    return STATUS_STYLES[contract.status] ?? STATUS_STYLES.PENDING
  }, [contract])

  if (loading) {
    return <section className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm">Loading contract details...</section>
  }

  if (error || !contract) {
    return (
      <section className="flex flex-col gap-4">
        <button
          type="button"
          onClick={() => navigate('/hr/contracts')}
          className="inline-flex w-fit items-center gap-2 rounded-full border border-[var(--border)] bg-white px-4 py-2 text-sm font-medium text-[var(--foreground)] shadow-sm transition-colors hover:border-[#D1353B] hover:text-[#D1353B]"
        >
          <FiArrowLeft className="h-4 w-4" />
          Back to Contracts
        </button>

        <div className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm">
          <h2 className="text-[1.18rem] font-semibold">Contract details unavailable</h2>
          <p className="mt-2 text-sm text-[var(--muted-foreground)]">{error || 'Contract not found.'}</p>
        </div>
      </section>
    )
  }

  return (
    <section className="flex flex-col gap-4">
      <button
        type="button"
        onClick={() => navigate('/hr/contracts')}
        className="inline-flex w-fit items-center gap-2 rounded-full border border-[var(--border)] bg-white px-4 py-2 text-sm font-medium text-[var(--foreground)] shadow-sm transition-colors hover:border-[#D1353B] hover:text-[#D1353B]"
      >
        <FiArrowLeft className="h-4 w-4" />
        Back to Contracts
      </button>

      <div className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[var(--border)] pb-4">
          <div>
            <p className="text-sm text-[var(--muted-foreground)]">Contract {contract.contract_number}</p>
            <h2 className="mt-1 text-[1.18rem] font-semibold">{contract.employee_name}</h2>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">Employee contract details</p>
          </div>

          <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${statusClass}`}>
            {STATUS_LABELS[contract.status] ?? contract.status}
          </span>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <article className="rounded-xl border border-[var(--border)] p-4">
            <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">Department</p>
            <p className="mt-1 font-medium">{contract.department ?? 'Unassigned'}</p>
          </article>
          <article className="rounded-xl border border-[var(--border)] p-4">
            <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">Contract Type</p>
            <p className="mt-1 font-medium">{TYPE_LABELS[contract.type]}</p>
          </article>
          <article className="rounded-xl border border-[var(--border)] p-4">
            <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">Start Date</p>
            <p className="mt-1 font-medium">{formatDate(contract.start_date)}</p>
          </article>
          <article className="rounded-xl border border-[var(--border)] p-4">
            <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">End Date</p>
            <p className="mt-1 font-medium">{formatDate(contract.end_date)}</p>
          </article>
          <article className="rounded-xl border border-[var(--border)] p-4">
            <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">Salary</p>
            <p className="mt-1 font-medium">{Number(contract.salary_ron).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} RON</p>
          </article>
          <article className="rounded-xl border border-[var(--border)] p-4">
            <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">Status</p>
            <p className="mt-1 font-medium">{STATUS_LABELS[contract.status] ?? contract.status}</p>
          </article>
        </div>
      </div>
    </section>
  )
}