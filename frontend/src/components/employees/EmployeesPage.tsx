import { useEffect, useMemo, useState } from 'react'

type DepartmentCount = {
  name: string
  count: number
}

type Employee = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
  is_active: boolean
  full_time: boolean
  department: null | {
    id: number
    name: string
    slug: string
  }
}

type PaginatedEmployees = {
  count: number
  next: string | null
  previous: string | null
  results: Employee[]
}

type EmployeeStats = {
  total: number
  active: number
  full_time: number
  departments: DepartmentCount[]
}

const EmployeesPage = () => {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [stats, setStats] = useState<EmployeeStats>({
    total: 0,
    active: 0,
    full_time: 0,
    departments: [],
  })
  const [departmentFilter, setDepartmentFilter] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  const fetchStats = async () => {
    const response = await fetch('/api/employees/stats/', {
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error(`Failed to load employee stats: ${response.status}`)
    }

    const data = (await response.json()) as EmployeeStats
    setStats(data)
  }

  const fetchEmployees = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
      })

      if (departmentFilter.trim()) {
        params.set('department', departmentFilter.trim())
      }
      if (activeFilter !== 'all') {
        params.set('is_active', activeFilter)
      }

      const response = await fetch(`/api/employees/?${params.toString()}`, {
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`Failed to load employees: ${response.status}`)
      }

      const data = (await response.json()) as PaginatedEmployees

      setEmployees(data.results)
      setTotal(data.count)
      await fetchStats()
    } catch (error) {
      console.error('Failed to load employees', error)
      setEmployees([])
      setTotal(0)
      setStats({ total: 0, active: 0, full_time: 0, departments: [] })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchEmployees()
  }, [page, departmentFilter, activeFilter])

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(total / 10))
  }, [total])

  return (
    <div className="dashboard-wrap">
      <div className="dashboard-header-row">
        <div>
          <h2>Employee Directory</h2>
          <p>Track headcount with real-time filters and aggregated stats.</p>
        </div>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span>Total Employees</span>
          <strong>{stats.total}</strong>
        </article>
        <article className="stat-card">
          <span>Active Employees</span>
          <strong>{stats.active}</strong>
        </article>
        <article className="stat-card">
          <span>Full-time Employees</span>
          <strong>{stats.full_time}</strong>
        </article>
      </div>

      <div className="employee-filters">
        <input
          value={departmentFilter}
          onChange={event => {
            setPage(1)
            setDepartmentFilter(event.target.value)
          }}
          placeholder="Filter by department slug (e.g. hr)"
          aria-label="Filter by department"
        />

        <select
          value={activeFilter}
          onChange={event => {
            setPage(1)
            setActiveFilter(event.target.value)
          }}
          aria-label="Filter by active status"
        >
          <option value="all">All statuses</option>
          <option value="true">Active only</option>
          <option value="false">Inactive only</option>
        </select>
      </div>

      {isLoading ? (
        <section className="module-card">Loading employees...</section>
      ) : employees.length === 0 ? (
        <section className="empty-state-card">
          <h3>No employees found</h3>
          <p>Try clearing filters or add employees so headcount can be tracked.</p>
          <button
            type="button"
            className="clear-filters-btn"
            onClick={() => {
              setDepartmentFilter('')
              setActiveFilter('all')
              setPage(1)
            }}
          >
            Clear Filters
          </button>
        </section>
      ) : (
        <>
          <section className="employee-list-card">
            <table className="employee-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Department</th>
                  <th>Status</th>
                  <th>Contract</th>
                </tr>
              </thead>
              <tbody>
                {employees.map(employee => (
                  <tr key={employee.id}>
                    <td>{`${employee.first_name} ${employee.last_name}`.trim() || employee.username}</td>
                    <td>{employee.email}</td>
                    <td>{employee.role}</td>
                    <td>{employee.department?.name ?? 'Unassigned'}</td>
                    <td>{employee.is_active ? 'Active' : 'Inactive'}</td>
                    <td>{employee.full_time ? 'Full-time' : 'Part-time'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <div className="employee-footer-row">
            <div className="department-counts">
              {stats.departments.map(dep => (
                <span key={dep.name} className="department-pill">{dep.name}: {dep.count}</span>
              ))}
            </div>

            <div className="pagination-controls">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage(current => Math.max(1, current - 1))}
              >
                Previous
              </button>
              <span>{`Page ${page} / ${totalPages}`}</span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage(current => Math.min(totalPages, current + 1))}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default EmployeesPage
