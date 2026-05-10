import React from 'react'

type Workflow = {
  id: number
  name: string
  trigger_type: string
  trigger_config: Record<string, string>
  is_active: boolean
  updated_at: string
}

const scheduleLabel = (w: Workflow): string => {
  const cfg = w.trigger_config
  if (cfg.day_of_week && cfg.time) {
    const day = cfg.day_of_week.charAt(0).toUpperCase() + cfg.day_of_week.slice(1)
    return `Every ${day} at ${cfg.time}`
  }
  if (w.trigger_type) return w.trigger_type.replace(/_/g, ' ')
  return 'Manual'
}

const WorkflowsPage = () => {
  const [workflows, setWorkflows] = React.useState<Workflow[]>([])
  const [loading, setLoading] = React.useState(true)
  const [toggling, setToggling] = React.useState<number | null>(null)

  React.useEffect(() => {
    fetch('/api/workflows/', { credentials: 'include' })
      .then(r => r.json())
      .then((data: Workflow[]) => setWorkflows(Array.isArray(data) ? data : []))
      .catch(() => setWorkflows([]))
      .finally(() => setLoading(false))
  }, [])

  const toggle = async (w: Workflow) => {
    setToggling(w.id)
    try {
      const res = await fetch(`/api/workflows/${w.id}/toggle/`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !w.is_active }),
      })
      if (res.ok) {
        const updated = await res.json()
        setWorkflows(prev => prev.map(x => x.id === w.id ? { ...x, is_active: updated.is_active } : x))
      }
    } finally {
      setToggling(null)
    }
  }

  return (
    <div className="space-y-6">
      <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">
        <h2 className="text-lg font-semibold">Workflows</h2>
        <p className="text-sm text-black/60 mt-1">Manage automated agents and scheduled processes.</p>

        {loading ? (
          <p className="text-sm text-black/60 mt-4">Loading workflows…</p>
        ) : workflows.length === 0 ? (
          <p className="text-sm text-black/60 mt-4">No workflows configured yet.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {workflows.map(w => (
              <div
                key={w.id}
                className="flex items-center justify-between gap-4 rounded-xl border border-[var(--border)] bg-white px-5 py-4"
              >
                <div className="flex items-center gap-4 min-w-0">
                  {/* Icon */}
                  <div className={`h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ${w.is_active ? 'bg-emerald-50' : 'bg-gray-100'}`}>
                    <svg className={`w-5 h-5 ${w.is_active ? 'text-emerald-600' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>

                  {/* Info */}
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">{w.name}</p>
                    <p className="text-xs text-black/50 mt-0.5">{scheduleLabel(w)}</p>
                  </div>
                </div>

                {/* Status + toggle */}
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${w.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
                    {w.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <button
                    onClick={() => toggle(w)}
                    disabled={toggling === w.id}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer focus:outline-none disabled:opacity-50 ${w.is_active ? 'bg-emerald-500' : 'bg-gray-200'}`}
                    title={w.is_active ? 'Disable workflow' : 'Enable workflow'}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${w.is_active ? 'translate-x-6' : 'translate-x-1'}`}
                    />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default WorkflowsPage
