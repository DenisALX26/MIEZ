import React from 'react'
import { workflowsApi, type Workflow, type WorkflowLog, type TriggerOption, type ActionOption, type WorkflowPayload } from '../../api/workflows'

// ── Icons ─────────────────────────────────────────────────────────────────────

const BoltIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
)

const PlusIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
)

const PencilIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  </svg>
)

const TrashIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
)

const ChevronDownIcon = ({ open }: { open: boolean }) => (
  <svg className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
)

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })

const EMPTY_PAYLOAD: WorkflowPayload = {
  name: '',
  trigger_type: '',
  trigger_config: {},
  actions: [],
  is_active: true,
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: () => void; disabled?: boolean }) {
  return (
    <button
      onClick={onChange}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer focus:outline-none disabled:opacity-50 ${checked ? 'bg-emerald-500' : 'bg-gray-200'}`}
    >
      <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`} />
    </button>
  )
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${active ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
      {active ? 'Active' : 'Inactive'}
    </span>
  )
}

function SuccessBadge({ ok }: { ok: boolean }) {
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${ok ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'}`}>
      {ok ? 'Success' : 'Failed'}
    </span>
  )
}

// ── Workflow Form Modal ───────────────────────────────────────────────────────

type ModalProps = {
  workflow?: Workflow
  triggers: TriggerOption[]
  actions: ActionOption[]
  onClose: () => void
  onSaved: (w: Workflow) => void
}

function WorkflowModal({ workflow, triggers, actions, onClose, onSaved }: ModalProps) {
  const isEdit = !!workflow
  const [form, setForm] = React.useState<WorkflowPayload>(
    workflow
      ? { name: workflow.name, trigger_type: workflow.trigger_type, trigger_config: workflow.trigger_config, actions: workflow.actions, is_active: workflow.is_active }
      : EMPTY_PAYLOAD
  )
  const [saving, setSaving] = React.useState(false)
  const [error, setError] = React.useState('')

  const set = (key: keyof WorkflowPayload, val: unknown) =>
    setForm(prev => ({ ...prev, [key]: val }))

  const toggleAction = (val: string) => {
    set('actions', form.actions.includes(val)
      ? form.actions.filter(a => a !== val)
      : [...form.actions, val])
  }

  const save = async () => {
    setError('')
    setSaving(true)
    try {
      const saved = isEdit
        ? await workflowsApi.update(workflow!.id, form)
        : await workflowsApi.create(form)
      onSaved(saved)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-base font-semibold">{isEdit ? 'Edit Workflow' : 'New Workflow'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">✕</button>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              value={form.name}
              onChange={e => set('name', e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. New Order Alert"
            />
          </div>

          {/* Trigger type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Trigger</label>
            <select
              value={form.trigger_type}
              onChange={e => set('trigger_type', e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">— select trigger —</option>
              {triggers.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          {/* Trigger config — contextual */}
          {(form.trigger_type === 'DAILY_AT_TIME' || form.trigger_type === 'WEEKLY_AT_TIME') && (
            <div className="grid grid-cols-2 gap-3">
              {form.trigger_type === 'WEEKLY_AT_TIME' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Day of week</label>
                  <select
                    value={(form.trigger_config.day_of_week as string) || ''}
                    onChange={e => set('trigger_config', { ...form.trigger_config, day_of_week: e.target.value })}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {['monday','tuesday','wednesday','thursday','friday','saturday','sunday'].map(d => (
                      <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                    ))}
                  </select>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Time (HH:MM)</label>
                <input
                  type="time"
                  value={(form.trigger_config.time as string) || ''}
                  onChange={e => set('trigger_config', { ...form.trigger_config, time: e.target.value })}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          {form.trigger_type === 'ORDER_EXCEEDS_THRESHOLD' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Threshold (RON)</label>
              <input
                type="number"
                value={(form.trigger_config.threshold as number) || ''}
                onChange={e => set('trigger_config', { ...form.trigger_config, threshold: Number(e.target.value) })}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="10000"
              />
            </div>
          )}

          {form.trigger_type === 'CONTRACT_EXPIRES' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Days ahead</label>
              <input
                type="number"
                value={(form.trigger_config.days_ahead as number) || ''}
                onChange={e => set('trigger_config', { ...form.trigger_config, days_ahead: Number(e.target.value) })}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="30"
              />
            </div>
          )}

          {/* Actions multi-select */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Actions</label>
            <div className="grid grid-cols-2 gap-2">
              {actions.map(a => (
                <label key={a.value} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.actions.includes(a.value)}
                    onChange={() => toggleAction(a.value)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  {a.label}
                </label>
              ))}
            </div>
          </div>

          {/* Active toggle */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Active</span>
            <Toggle checked={form.is_active} onChange={() => set('is_active', !form.is_active)} />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>

        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="px-4 py-2 text-sm rounded-lg bg-gray-900 text-white hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Create workflow'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Delete Confirmation Dialog ────────────────────────────────────────────────

function DeleteDialog({ workflow, onClose, onDeleted }: { workflow: Workflow; onClose: () => void; onDeleted: (id: number) => void }) {
  const [deleting, setDeleting] = React.useState(false)
  const [error, setError] = React.useState('')

  const confirm = async () => {
    setDeleting(true)
    try {
      await workflowsApi.remove(workflow.id)
      onDeleted(workflow.id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Delete failed')
      setDeleting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 className="text-base font-semibold">Delete workflow?</h2>
        <p className="text-sm text-gray-600">
          Are you sure you want to delete <strong>{workflow.name}</strong>?
          {workflow.is_active && (
            <span className="block mt-1 text-amber-600">⚠ This workflow is currently active.</span>
          )}
        </p>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
            Cancel
          </button>
          <button
            onClick={confirm}
            disabled={deleting}
            className="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Log Row (collapsible) ─────────────────────────────────────────────────────

function LogRow({ log }: { log: WorkflowLog }) {
  const [open, setOpen] = React.useState(false)
  return (
    <>
      <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => setOpen(o => !o)}>
        <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{fmtDate(log.triggered_at)}</td>
        <td className="px-4 py-3 text-sm font-medium text-gray-900">{log.workflow_name}</td>
        <td className="px-4 py-3 text-sm text-gray-500">{log.trigger_type.replace(/_/g, ' ')}</td>
        <td className="px-4 py-3"><SuccessBadge ok={log.success} /></td>
        <td className="px-4 py-3 text-gray-400"><ChevronDownIcon open={open} /></td>
      </tr>
      {open && (
        <tr>
          <td colSpan={5} className="px-4 pb-3">
            <div className="rounded-lg bg-gray-50 border border-gray-100 divide-y divide-gray-100">
              {log.actions_log.map((a, i) => (
                <div key={i} className="flex items-start gap-3 px-4 py-2.5">
                  <span className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${a.success ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-gray-700">{a.action.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-gray-500 truncate">{a.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function WorkflowsPage() {
  const [tab, setTab] = React.useState<'workflows' | 'logs'>('workflows')
  const [workflows, setWorkflows] = React.useState<Workflow[]>([])
  const [logs, setLogs] = React.useState<WorkflowLog[]>([])
  const [triggers, setTriggers] = React.useState<TriggerOption[]>([])
  const [actions, setActions] = React.useState<ActionOption[]>([])
  const [loading, setLoading] = React.useState(true)
  const [toggling, setToggling] = React.useState<number | null>(null)
  const [modal, setModal] = React.useState<'create' | 'edit' | null>(null)
  const [editing, setEditing] = React.useState<Workflow | null>(null)
  const [deleting, setDeleting] = React.useState<Workflow | null>(null)

  React.useEffect(() => {
    const load = async () => {
      try {
        const [wf, tr, ac] = await Promise.all([
          workflowsApi.list(),
          workflowsApi.triggers(),
          workflowsApi.actions(),
        ])
        setWorkflows(wf)
        setTriggers(tr)
        setActions(ac)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const loadLogs = async () => {
    try {
      const data = await workflowsApi.logs()
      setLogs(data)
    } catch {
      setLogs([])
    }
  }

  React.useEffect(() => {
    if (tab === 'logs') loadLogs()
  }, [tab])

  const toggle = async (w: Workflow) => {
    setToggling(w.id)
    try {
      const updated = await workflowsApi.toggle(w.id, !w.is_active)
      setWorkflows(prev => prev.map(x => x.id === w.id ? { ...x, is_active: updated.is_active } : x))
    } finally {
      setToggling(null)
    }
  }

  const onSaved = (saved: Workflow) => {
    setWorkflows(prev =>
      prev.some(w => w.id === saved.id)
        ? prev.map(w => w.id === saved.id ? saved : w)
        : [...prev, saved]
    )
    setModal(null)
    setEditing(null)
  }

  const onDeleted = (id: number) => {
    setWorkflows(prev => prev.filter(w => w.id !== id))
    setDeleting(null)
  }

  const activeCount = workflows.filter(w => w.is_active).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Automated Workflow Engine</h2>
            <p className="text-sm text-black/60 mt-1">
              {activeCount} active · {workflows.length} total
            </p>
          </div>
          <button
            onClick={() => { setEditing(null); setModal('create') }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-900 text-white text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            <PlusIcon />
            New workflow
          </button>
        </div>

        {/* Tabs */}
        <div className="mt-5 flex gap-1 border-b border-gray-100">
          {(['workflows', 'logs'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              {t === 'workflows' ? 'Workflows' : 'Execution Log'}
            </button>
          ))}
        </div>
      </section>

      {/* Workflows tab */}
      {tab === 'workflows' && (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">
          {loading ? (
            <p className="text-sm text-black/60">Loading…</p>
          ) : workflows.length === 0 ? (
            <p className="text-sm text-black/60">No workflows yet. Create one above.</p>
          ) : (
            <div className="space-y-3">
              {workflows.map(w => (
                <div
                  key={w.id}
                  className={`flex items-center justify-between gap-4 rounded-xl border px-5 py-4 transition-opacity ${w.is_active ? 'border-[var(--border)] bg-white' : 'border-gray-100 bg-gray-50 opacity-70'}`}
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <div className={`h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ${w.is_active ? 'bg-emerald-50' : 'bg-gray-100'}`}>
                      <BoltIcon className={`w-5 h-5 ${w.is_active ? 'text-emerald-600' : 'text-gray-400'}`} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-gray-900 truncate">{w.name}</p>
                      <p className="text-xs text-black/50 mt-0.5">{w.trigger_label}</p>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {w.action_labels.map(a => (
                          <span key={a} className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">{a}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {w.last_triggered_at && (
                      <span className="text-xs text-gray-400 hidden sm:block">
                        Last: {fmtDate(w.last_triggered_at)}
                      </span>
                    )}
                    <StatusBadge active={w.is_active} />
                    <button
                      onClick={() => { setEditing(w); setModal('edit') }}
                      className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                      title="Edit"
                    >
                      <PencilIcon />
                    </button>
                    <button
                      onClick={() => setDeleting(w)}
                      className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                      title="Delete"
                    >
                      <TrashIcon />
                    </button>
                    <Toggle
                      checked={w.is_active}
                      onChange={() => toggle(w)}
                      disabled={toggling === w.id}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Logs tab */}
      {tab === 'logs' && (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl overflow-hidden">
          {logs.length === 0 ? (
            <p className="text-sm text-black/60 p-5">No execution logs yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Triggered at', 'Workflow', 'Trigger', 'Result', ''].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {logs.map(l => <LogRow key={l.id} log={l} />)}
              </tbody>
            </table>
          )}
        </section>
      )}

      {/* Modals */}
      {(modal === 'create' || modal === 'edit') && (
        <WorkflowModal
          workflow={modal === 'edit' ? editing ?? undefined : undefined}
          triggers={triggers}
          actions={actions}
          onClose={() => { setModal(null); setEditing(null) }}
          onSaved={onSaved}
        />
      )}
      {deleting && (
        <DeleteDialog
          workflow={deleting}
          onClose={() => setDeleting(null)}
          onDeleted={onDeleted}
        />
      )}
    </div>
  )
}
