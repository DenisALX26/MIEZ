import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../../context/AuthContext'

type AttendanceStatus = 'PRESENT' | 'ABSENT' | 'REMOTE' | 'LEAVE' | null

type AttendanceGridRow = {
  employee_id: number
  employee_name: string
  department: string | null
  statuses: Record<string, AttendanceStatus>
}

type AttendanceResponse = {
  week_start: string
  week_end: string
  days: string[]
  grid: AttendanceGridRow[]
}

const statusMeta: Record<Exclude<AttendanceStatus, null>, { label: string; short: string; className: string }> = {
  PRESENT: {
    label: 'Present',
    short: 'P',
    className: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  },
  REMOTE: {
    label: 'Remote',
    short: 'P',
    className: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  },
  ABSENT: {
    label: 'Absent',
    short: 'A',
    className: 'bg-rose-100 text-rose-700 border-rose-200',
  },
  LEAVE: {
    label: 'Leave',
    short: 'L',
    className: 'bg-amber-100 text-amber-700 border-amber-200',
  },
}

const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const isWeekend = (dateValue: string) => {
  const date = new Date(dateValue)
  const day = date.getDay()
  return day === 0 || day === 6
}

const formatDateShort = (dateValue: string) => {
  const date = new Date(dateValue)
  if (Number.isNaN(date.getTime())) {
    return dateValue
  }

  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

const getMondayOfWeek = (dateValue: Date) => {
  const date = new Date(dateValue)
  const day = date.getDay()
  const diff = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + diff)
  date.setHours(0, 0, 0, 0)
  return date
}

const addDays = (dateValue: Date, days: number) => {
  const date = new Date(dateValue)
  date.setDate(date.getDate() + days)
  return date
}

const formatWeekTitle = (weekStart: Date) => {
  const monthYear = weekStart.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
  const weekNumber = Math.ceil(weekStart.getDate() / 7)
  return `${monthYear} — Week ${weekNumber}`
}

const HrAttendancePage = () => {
  const { user } = useAuth()
  const [selectedWeekStart, setSelectedWeekStart] = useState(() => getMondayOfWeek(new Date()))
  const [data, setData] = useState<AttendanceResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadAttendance = async () => {
      try {
        setIsLoading(true)
        setError('')

        const weekParam = selectedWeekStart.toISOString().slice(0, 10)
        const response = await fetch(`/api/attendance/?week=${weekParam}`, {
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error(`Attendance request failed: ${response.status}`)
        }

        const payload = (await response.json()) as AttendanceResponse
        setData(payload)
      } catch (fetchError) {
        console.error('Failed to load attendance grid', fetchError)
        setError('Could not load attendance data right now.')
        setData(null)
      } finally {
        setIsLoading(false)
      }
    }

    loadAttendance()
  }, [selectedWeekStart])

  const dayInfo = useMemo(() => {
    return (data?.days ?? []).map((dayValue, index) => ({
      value: dayValue,
      label: weekdayLabels[index] ?? '',
      isWeekend: isWeekend(dayValue),
    }))
  }, [data?.days])

  const summary = useMemo(() => {
    const rows = data?.grid ?? []
    const weekdays = dayInfo.filter(day => !day.isWeekend)
    const workdayCount = Math.max(weekdays.length, 1)
    const totalPossible = rows.length * workdayCount

    let presentCount = 0
    let absentCount = 0

    for (const row of rows) {
      for (const day of weekdays) {
        const status = row.statuses[day.value]
        if (status === 'PRESENT') {
          presentCount += 1
        } else if (status === 'ABSENT') {
          absentCount += 1
        }
      }
    }

    return {
      avgAttendance: totalPossible > 0 ? Math.round((presentCount / totalPossible) * 1000) / 10 : 0,
      onLeaveEmployees: rows.filter(row => weekdays.some(day => row.statuses[day.value] === 'LEAVE')).length,
      unexcusedAbsences: absentCount,
    }
  }, [data?.grid, dayInfo])

  const presentCountForRow = (row: AttendanceGridRow) => {
    return dayInfo.filter(day => !day.isWeekend && (row.statuses[day.value] === 'PRESENT' || row.statuses[day.value] === 'REMOTE')).length
  }

  const currentWeekLabel = formatWeekTitle(selectedWeekStart)
  const weekStartIso = selectedWeekStart.toISOString().slice(0, 10)

  if (user?.role !== 'HR' && user?.role !== 'CEO') {
    return (
      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
        <h2 className="text-[1.1rem] font-semibold">Attendance</h2>
        <p className="text-[0.92rem] text-[var(--muted-foreground)] mt-1">This page is available for HR and CEO only.</p>
      </section>
    )
  }

  return (
    <section className="flex flex-col gap-4">
      <header className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-[1.22rem] font-semibold">Attendance & Timesheets</h2>
            <p className="text-[0.92rem] text-[var(--muted-foreground)]">
              Weekly attendance grid per employee with presence and leave at a glance.
            </p>
          </div>

          <div className="inline-flex items-center gap-2 flex-wrap">
            <button
              type="button"
              className="min-h-[40px] rounded-[10px] border border-[var(--border)] bg-[var(--card)] px-3 font-semibold"
              onClick={() => setSelectedWeekStart(current => addDays(current, -7))}
            >
              Previous week
            </button>
            <div className="min-h-[40px] px-4 rounded-[10px] border border-[var(--border)] bg-[var(--card)] flex items-center font-semibold">
              {currentWeekLabel}
            </div>
            <button
              type="button"
              className="min-h-[40px] rounded-[10px] border border-[var(--border)] bg-[var(--card)] px-3 font-semibold"
              onClick={() => setSelectedWeekStart(current => addDays(current, 7))}
            >
              Next week
            </button>
          </div>
        </div>

        <div className="text-sm text-[var(--muted-foreground)]">Week start: {weekStartIso}</div>
      </header>

      <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
        <div className="flex items-center gap-4 flex-wrap text-sm">
          <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-emerald-500" /> Present</span>
          <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-amber-500" /> Leave</span>
          <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-rose-500" /> Absent</span>
          <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-slate-400" /> Weekend</span>
        </div>
      </section>

      {isLoading ? (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">Loading attendance grid...</section>
      ) : error ? (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 text-red-600">{error}</section>
      ) : (
        <>
          <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl overflow-hidden">
            <div className="overflow-auto">
              <table className="min-w-full border-collapse">
                <thead>
                  <tr className="bg-[var(--muted)]/30">
                    <th className="sticky left-0 z-10 bg-[var(--card)] text-left px-4 py-3 border-b border-[var(--border)] min-w-[220px]">Employee</th>
                    <th className="sticky left-[220px] z-10 bg-[var(--card)] text-left px-4 py-3 border-b border-[var(--border)] min-w-[180px]">Department</th>
                    {dayInfo.map(day => (
                      <th key={day.value} className="text-center px-3 py-3 border-b border-[var(--border)] min-w-[84px]">
                        <div className="text-[0.82rem] font-semibold">{day.label}</div>
                        <div className="text-[0.75rem] text-[var(--muted-foreground)]">{formatDateShort(day.value)}</div>
                      </th>
                    ))}
                    <th className="text-center px-4 py-3 border-b border-[var(--border)] min-w-[120px]">Present count</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.grid ?? []).map(row => (
                    <tr key={row.employee_id} className="hover:bg-black/5 transition-colors">
                      <td className="sticky left-0 z-10 bg-[var(--card)] px-4 py-3 border-b border-[var(--border)] font-medium">{row.employee_name}</td>
                      <td className="sticky left-[220px] z-10 bg-[var(--card)] px-4 py-3 border-b border-[var(--border)] text-[0.92rem] text-[var(--muted-foreground)]">{row.department ?? 'Unassigned'}</td>
                      {dayInfo.map(day => {
                        if (day.isWeekend) {
                          return (
                            <td key={day.value} className="px-3 py-3 border-b border-[var(--border)] text-center text-slate-400 font-semibold">
                              —
                            </td>
                          )
                        }

                        const status = row.statuses[day.value]
                        if (!status) {
                          return (
                            <td key={day.value} className="px-3 py-3 border-b border-[var(--border)] text-center text-slate-400 font-semibold">
                              —
                            </td>
                          )
                        }

                        const meta = statusMeta[status]
                        return (
                          <td key={day.value} className="px-3 py-3 border-b border-[var(--border)] text-center">
                            <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full border text-[0.82rem] font-bold ${meta.className}`} title={meta.label}>
                              {meta.short}
                            </span>
                          </td>
                        )
                      })}
                      <td className="px-4 py-3 border-b border-[var(--border)] text-center font-semibold">{presentCountForRow(row)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <article className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
              <span className="text-[0.82rem] text-[var(--muted-foreground)]">Avg Attendance This Week (%)</span>
              <strong className="block text-[1.6rem] mt-1">{summary.avgAttendance}%</strong>
            </article>
            <article className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
              <span className="text-[0.82rem] text-[var(--muted-foreground)]">Employees on Leave</span>
              <strong className="block text-[1.6rem] mt-1">{summary.onLeaveEmployees}</strong>
            </article>
            <article className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
              <span className="text-[0.82rem] text-[var(--muted-foreground)]">Unexcused Absences</span>
              <strong className="block text-[1.6rem] mt-1">{summary.unexcusedAbsences}</strong>
            </article>
          </div>
        </>
      )}
    </section>
  )
}

export default HrAttendancePage
