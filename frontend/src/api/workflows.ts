export type Workflow = {
  id: number
  name: string
  trigger_type: string
  trigger_label: string
  trigger_config: Record<string, string | number>
  actions: string[]
  action_labels: string[]
  is_active: boolean
  last_triggered_at: string | null
  created_at: string
  updated_at: string
}

export type WorkflowLog = {
  id: number
  workflow: number
  workflow_name: string
  triggered_at: string
  trigger_type: string
  actions_log: { action: string; success: boolean; message: string }[]
  success: boolean
}

export type TriggerOption = { value: string; label: string }
export type ActionOption  = { value: string; label: string }

export type WorkflowPayload = {
  name: string
  trigger_type: string
  trigger_config: Record<string, string | number>
  actions: string[]
  is_active: boolean
}

const OPTS: RequestInit = { credentials: 'include', headers: { 'Content-Type': 'application/json' } }

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { ...OPTS, ...init, headers: { ...OPTS.headers, ...init?.headers } })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? JSON.stringify(err))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const workflowsApi = {
  list: ()                           => req<Workflow[]>('/api/workflows/'),
  create: (data: WorkflowPayload)    => req<Workflow>('/api/workflows/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<WorkflowPayload>) =>
    req<Workflow>(`/api/workflows/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
  remove: (id: number)               => req<void>(`/api/workflows/${id}/`, { method: 'DELETE' }),
  toggle: (id: number, is_active: boolean) =>
    req<{ id: number; is_active: boolean }>(`/api/workflows/${id}/toggle/`, { method: 'PATCH', body: JSON.stringify({ is_active }) }),
  triggers: ()                       => req<TriggerOption[]>('/api/workflows/triggers/'),
  actions: ()                        => req<ActionOption[]>('/api/workflows/actions/'),
  logs: ()                           => req<WorkflowLog[]>('/api/workflows/logs/'),
}
