import React from 'react'
import { useAuth } from '../../context/AuthContext'

type HrKpiResponse = {
  total_employees: number
  new_hires_this_month: number
  leave_requests_this_month: number
  pending_leave_requests: number
  full_time_employees: number
  non_full_time_employees: number
  retention_rate: number
  active_employees: number
}

type AgentReport = {
  id: number
  name: string
  slug: string
  period: string
  generated_at: string
  digest_data: {
    week: string
    week_start: string
    week_end: string
    content: string
    tool_calls: number
  } | null
}

type Tab = 'overview' | 'agent-reports'

type DepartmentHeadcount = {
  department: string
  total: number
  active: number
  on_leave: number
  utilisation_pct: number
}

type AttendanceWeek = {
  week_start: string
  attendance_rate: number
}

type CeoSummaryResponse = {
  department_headcount: DepartmentHeadcount[]
  attendance_rate_weeks: AttendanceWeek[]
}

type Employee = {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  role: string
  position: string
  employment_type: string
  department: { id: number; name: string } | null
  start_date: string
}

const UsersIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
  </svg>
)

const formatDate = (value: string) =>
  new Date(value).toLocaleDateString('ro-RO')

const roleBadge: Record<string, string> = {
  CEO:       'bg-rose-50 text-rose-700 border border-rose-200',
  HR:        'bg-purple-50 text-purple-700 border border-purple-200',
  IT:        'bg-blue-50 text-blue-700 border border-blue-200',
  SALES:     'bg-emerald-50 text-emerald-700 border border-emerald-200',
  INVENTORY: 'bg-amber-50 text-amber-700 border border-amber-200',
}

const HrDashboard = () => {
  const { user } = useAuth()
  const isCeo = user?.role === 'CEO'

  const [activeTab, setActiveTab] = React.useState<Tab>('overview')

  const [kpis, setKpis] = React.useState<HrKpiResponse | null>(null)
  const [loadingKpis, setLoadingKpis] = React.useState(true)
  const [kpisError, setKpisError] = React.useState('')

  const [ceoSummary, setCeoSummary] = React.useState<CeoSummaryResponse | null>(null)
  const [loadingSummary, setLoadingSummary] = React.useState(false)

  const [employees, setEmployees] = React.useState<Employee[]>([])
  const [loadingEmployees, setLoadingEmployees] = React.useState(false)
  const [employeesError, setEmployeesError] = React.useState('')
  const [empSearch, setEmpSearch] = React.useState('')

  const [agentReports, setAgentReports] = React.useState<AgentReport[]>([])
  const [loadingReports, setLoadingReports] = React.useState(false)
  const [expandedReport, setExpandedReport] = React.useState<number | null>(null)

  // KPIs
  React.useEffect(() => {
    fetch('/api/hr/dashboard/', { credentials: 'include' })
      .then(r => { if (!r.ok) throw new Error(String(r.status)); return r.json() })
      .then((data: HrKpiResponse) => setKpis(data))
      .catch(() => setKpisError('Could not load HR KPI data.'))
      .finally(() => setLoadingKpis(false))
  }, [])

  // CEO summary (department headcount + attendance trend)
  React.useEffect(() => {
    if (!isCeo) return
    setLoadingSummary(true)
    fetch('/api/hr/ceo-summary/', { credentials: 'include' })
      .then(r => r.json())
      .then((data: CeoSummaryResponse) => setCeoSummary(data))
      .catch(console.error)
      .finally(() => setLoadingSummary(false))
  }, [isCeo])

  // Employee list
  React.useEffect(() => {
    if (!isCeo) return
    setLoadingEmployees(true)
    fetch('/api/employees/?page_size=50', { credentials: 'include' })
      .then(r => r.json())
      .then(data => setEmployees(Array.isArray(data.results) ? data.results : Array.isArray(data) ? data : []))
      .catch(() => setEmployeesError('Could not load employees.'))
      .finally(() => setLoadingEmployees(false))
  }, [isCeo])

  // Agent reports (lazy — only when tab is active)
  React.useEffect(() => {
    if (activeTab !== 'agent-reports') return
    setLoadingReports(true)
    fetch('/api/reports/?category=HR', { credentials: 'include' })
      .then(r => r.json())
      .then((data: AgentReport[]) => setAgentReports(Array.isArray(data) ? data : []))
      .catch(() => setAgentReports([]))
      .finally(() => setLoadingReports(false))
  }, [activeTab])

  const filteredEmployees = React.useMemo(() => {
    if (!empSearch.trim()) return employees
    const q = empSearch.toLowerCase()
    return employees.filter(e =>
      `${e.first_name} ${e.last_name}`.toLowerCase().includes(q) ||
      e.position.toLowerCase().includes(q) ||
      e.role.toLowerCase().includes(q)
    )
  }, [employees, empSearch])

  const maxAttendance = React.useMemo(
    () => Math.max(...(ceoSummary?.attendance_rate_weeks.map(w => w.attendance_rate) ?? [1]), 1),
    [ceoSummary]
  )

  const kpiCards = [
    { title: 'Total Employees',   value: kpis?.total_employees ?? 0,         sub: `+${kpis?.new_hires_this_month ?? 0} this month`,             color: 'text-blue-600',   bg: 'bg-blue-50' },
    { title: 'Leave Requests',    value: kpis?.leave_requests_this_month ?? 0, sub: `${kpis?.pending_leave_requests ?? 0} pending approval`,     color: 'text-orange-600', bg: 'bg-orange-50' },
    { title: 'Full-Time',         value: kpis?.full_time_employees ?? 0,      sub: `${kpis?.non_full_time_employees ?? 0} non full-time`,         color: 'text-purple-600', bg: 'bg-purple-50' },
    { title: 'Retention Rate',    value: `${(kpis?.retention_rate ?? 0).toFixed(1)}%`, sub: `${kpis?.active_employees ?? 0}/${kpis?.total_employees ?? 0} active`, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  ]

  const formatReportDate = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })

  return (
    <div className="space-y-6">

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-[var(--border)]">
        {(['overview', 'agent-reports'] as Tab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors cursor-pointer ${
              activeTab === tab
                ? 'bg-[var(--card)] border border-b-white border-[var(--border)] -mb-px text-gray-900'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'overview' ? 'Overview' : 'Agent Reports'}
          </button>
        ))}
      </div>

      {activeTab === 'agent-reports' && (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 space-y-4">
          <div>
            <h2 className="text-lg font-semibold">HR Agent Reports</h2>
            <p className="text-sm text-black/60 mt-1">Weekly digests generated by the autonomous HR Insights Agent.</p>
          </div>
          {loadingReports ? (
            <p className="text-sm text-black/60">Loading reports…</p>
          ) : agentReports.length === 0 ? (
            <p className="text-sm text-black/60">No HR agent reports yet. The agent runs every Monday at 06:00.</p>
          ) : (
            <ul className="space-y-3">
              {agentReports.map(report => (
                <li key={report.id} className="rounded-xl border border-[var(--border)] bg-white overflow-hidden">
                  <button
                    onClick={() => setExpandedReport(expandedReport === report.id ? null : report.id)}
                    className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors cursor-pointer"
                  >
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{report.name}</p>
                      <p className="text-xs text-black/50 mt-0.5">
                        {report.period} · Generated {formatReportDate(report.generated_at)}
                        {report.digest_data?.tool_calls != null && ` · ${report.digest_data.tool_calls} tool calls`}
                      </p>
                    </div>
                    <span className="text-gray-400 text-sm ml-4 shrink-0">
                      {expandedReport === report.id ? '▲' : '▼'}
                    </span>
                  </button>
                  {expandedReport === report.id && report.digest_data?.content && (
                    <div className="px-4 pb-4 pt-0 border-t border-[var(--border)]">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap font-sans leading-relaxed pt-3">
                        {report.digest_data.content}
                      </pre>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {activeTab === 'overview' && (
      <>

      {/* KPI Cards */}
      <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">
        <h2 className="text-lg font-semibold">HR Dashboard</h2>
        <p className="text-sm text-black/60 mt-1">Human resources metrics and headcount overview.</p>

        {loadingKpis ? (
          <p className="text-sm text-black/60 mt-3">Loading KPI data…</p>
        ) : kpisError ? (
          <p className="text-sm text-red-600 mt-3">{kpisError}</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
            {kpiCards.map(card => (
              <div key={card.title} className="rounded-xl border border-[var(--border)] bg-white p-4">
                <p className="text-xs uppercase tracking-wide text-black/50">{card.title}</p>
                <p className="text-2xl font-semibold mt-1">{card.value}</p>
                <p className="text-xs mt-1 text-black/60">{card.sub}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* CEO-only: Department Headcount + Attendance Trend */}
      {isCeo && (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold">Department Overview</h3>
              <p className="text-sm text-black/60 mt-1">Headcount and 6-week attendance rate by department.</p>
            </div>
          </div>

          {loadingSummary ? (
            <p className="text-sm text-black/60 mt-3">Loading summary…</p>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 mt-4">

              {/* Department headcount table */}
              <div className="xl:col-span-2 rounded-xl border border-[var(--border)] bg-white overflow-hidden">
                <p className="text-xs uppercase tracking-wide text-black/50 px-4 pt-4 pb-2">Headcount by department</p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-t border-[var(--border)]">
                      {['Department', 'Total', 'Active', 'On Leave', 'Utilisation'].map(h => (
                        <th key={h} className="text-left px-4 py-2 text-xs font-medium text-black/50">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(ceoSummary?.department_headcount ?? []).map(row => (
                      <tr key={row.department} className="border-t border-[var(--border)] hover:bg-gray-50">
                        <td className="px-4 py-2.5 font-medium">{row.department}</td>
                        <td className="px-4 py-2.5">{row.total}</td>
                        <td className="px-4 py-2.5 text-emerald-700">{row.active}</td>
                        <td className="px-4 py-2.5 text-orange-600">{row.on_leave}</td>
                        <td className="px-4 py-2.5">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                              <div
                                className="bg-blue-500 h-1.5 rounded-full"
                                style={{ width: `${row.utilisation_pct}%` }}
                              />
                            </div>
                            <span className="text-xs font-semibold w-10 text-right">{row.utilisation_pct}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Attendance rate 6-week trend */}
              <div className="rounded-xl border border-[var(--border)] bg-white p-4">
                <p className="text-xs uppercase tracking-wide text-black/50 mb-3">Attendance rate — last 6 weeks</p>
                <div className="h-44 flex items-end gap-1.5">
                  {(ceoSummary?.attendance_rate_weeks ?? []).map(week => {
                    const height = (week.attendance_rate / maxAttendance) * 100
                    const label = new Date(week.week_start).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
                    return (
                      <div key={week.week_start} className="flex-1 flex flex-col items-center justify-end h-full">
                        <span className="text-[9px] text-black/50 mb-1">{week.attendance_rate}%</span>
                        <div
                          className="w-full rounded-t-md bg-purple-400/80 border border-purple-500/20"
                          style={{ height: `${Math.max(height, 4)}%` }}
                        />
                        <span className="text-[9px] text-black/50 mt-1 text-center">{label}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {/* CEO-only: Employee List */}
      {isCeo && (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <UsersIcon />
                All Employees
              </h3>
              <p className="text-sm text-black/60 mt-1">Full roster across all departments.</p>
            </div>
            <span className="text-sm text-black/50">{filteredEmployees.length} of {employees.length}</span>
          </div>

          <input
            value={empSearch}
            onChange={e => setEmpSearch(e.target.value)}
            placeholder="Search by name, position, or role…"
            className="w-full max-w-sm rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-sm"
          />

          {loadingEmployees ? (
            <p className="text-sm text-black/60">Loading employees…</p>
          ) : employeesError ? (
            <p className="text-sm text-red-600">{employeesError}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-y-1.5">
                <thead>
                  <tr>
                    {['Name', 'Position', 'Department', 'Role', 'Type', 'Start Date'].map(h => (
                      <th key={h} className="text-left text-xs uppercase tracking-wide text-black/50 px-3">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredEmployees.map(emp => (
                    <tr key={emp.id} className="bg-white border border-[var(--border)]">
                      <td className="px-3 py-2.5">
                        <p className="text-sm font-semibold">{emp.first_name} {emp.last_name}</p>
                        <p className="text-xs text-black/50">{emp.email}</p>
                      </td>
                      <td className="px-3 py-2.5 text-sm">{emp.position || '—'}</td>
                      <td className="px-3 py-2.5 text-sm">{emp.department?.name ?? '—'}</td>
                      <td className="px-3 py-2.5">
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${roleBadge[emp.role] ?? 'bg-gray-100 text-gray-600'}`}>
                          {emp.role}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-sm text-black/60">{emp.employment_type?.replace('_', ' ') ?? '—'}</td>
                      <td className="px-3 py-2.5 text-sm text-black/60">{formatDate(emp.start_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      </>
      )}
    </div>
  )
}

export default HrDashboard
