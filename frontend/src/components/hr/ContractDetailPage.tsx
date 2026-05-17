import { FiArrowLeft } from 'react-icons/fi'
import { useNavigate, useParams } from 'react-router-dom'

export default function ContractDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()

  return (
    <section className="flex flex-col gap-4">
      <button
        type="button"
        onClick={() => navigate('/hr/contracts')}
        className="inline-flex w-fit items-center gap-2 rounded-full border border-[var(--border)] bg-white px-4 py-2 text-sm font-medium text-[var(--foreground)] shadow-sm transition-colors hover:border-[#D1353B] hover:text-[#D1353B]"
      >
        <FiArrowLeft className="h-4 w-4" />
        Back to contracts
      </button>

      <div className="rounded-2xl border border-[var(--border)] bg-white p-5 shadow-sm">
        <h2 className="text-[1.18rem] font-semibold">Contract detail coming soon</h2>
        <p className="mt-2 text-sm text-[var(--muted-foreground)]">
          Contract {id ? `#${id}` : 'selected'} will open a detail view in a future sprint.
        </p>
      </div>
    </section>
  )
}