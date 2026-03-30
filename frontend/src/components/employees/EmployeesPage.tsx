import { useEffect, useMemo, useState } from 'react'

type DepartmentCount = {
  name: string
  count: number
}

type Department = {
  id: number
  name: string
  slug: string
}

type Employee = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string
  position: string
  employment_type: string
  start_date: string
  salary_ron: string
  address: string
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

type EmployeeFormData = {
  first_name: string
  last_name: string
  email: string
  phone: string
  department: string
  position: string
  employment_type: string
  start_date: string
  salary_ron: string
  address: string
  is_active: boolean
}

const initialFormData: EmployeeFormData = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '+40',
  department: '',
  position: '',
  employment_type: 'FULL_TIME',
  start_date: '',
  salary_ron: '',
  address: '',
  is_active: true,
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

  const [departments, setDepartments] = useState<Department[]>([])
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [formData, setFormData] = useState<EmployeeFormData>(initialFormData)
  const [formErrors, setFormErrors] = useState<Record<string, string[]>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [toastMessage, setToastMessage] = useState('')

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

  const fetchDepartments = async () => {
    try {
      const response = await fetch('/api/departments/', {
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`Failed to load departments: ${response.status}`)
      }

      const data = (await response.json()) as Department[]
      setDepartments(data)
    } catch (error) {
      console.error('Failed to load departments', error)
      setDepartments([])
    }
  }

  useEffect(() => {
    fetchEmployees()
  }, [page, departmentFilter, activeFilter])

  useEffect(() => {
    fetchDepartments()
  }, [])

  useEffect(() => {
    if (!toastMessage) {
      return
    }

    const timeout = window.setTimeout(() => {
      setToastMessage('')
    }, 2600)

    return () => window.clearTimeout(timeout)
  }, [toastMessage])

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(total / 10))
  }, [total])

  const handleFormChange = (field: keyof EmployeeFormData, value: string | boolean) => {
    setFormData(current => ({
      ...current,
      [field]: value,
    }))
  }

  const resetForm = () => {
    setFormData(initialFormData)
    setFormErrors({})
    setIsSubmitting(false)
  }

  const handleCancel = () => {
    resetForm()
    setIsFormOpen(false)
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSubmitting(true)
    setFormErrors({})

    const payload = {
      ...formData,
      department: Number(formData.department) || null,
      salary_ron: parseFloat(formData.salary_ron) || 0,
    }

    try {
      const response = await fetch('/api/employees/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (response.status === 400) {
        const data = await response.json()
        setFormErrors(data)
        return
      }

      if (!response.ok) {
        throw new Error(`Failed to create employee: ${response.status}`)
      }

      resetForm()
      setIsFormOpen(false)
      setToastMessage('Employee created successfully.')
      setPage(1)
      await fetchEmployees()
    } catch (error) {
      console.error('Failed to create employee', error)
      setFormErrors({ non_field_errors: ['Failed to create employee. Please retry.'] })
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderError = (field: keyof EmployeeFormData | 'non_field_errors') => {
    const errors = formErrors[field]
    if (!errors || errors.length === 0) {
      return null
    }

    return <p className="form-error">{errors[0]}</p>
  }

  return (
    <div className="dashboard-wrap">
      {toastMessage && <div className="success-toast">{toastMessage}</div>}

      <div className="dashboard-header-row employee-header-row">
        <div>
          <h2>Employee Directory</h2>
          <p>Track headcount with real-time filters and aggregated stats.</p>
        </div>
        <button type="button" className="create-employee-btn" onClick={() => setIsFormOpen(true)}>
          Register Employee
        </button>
      </div>

      {isFormOpen && (
        <section className="employee-form-card">
          <h3>New Employee</h3>
          <form className="employee-create-form" onSubmit={handleSubmit}>
            <input
              value={formData.first_name}
              onChange={event => handleFormChange('first_name', event.target.value)}
              placeholder="First name"
              aria-label="First name"
              required
            />
            <input
              value={formData.last_name}
              onChange={event => handleFormChange('last_name', event.target.value)}
              placeholder="Last name"
              aria-label="Last name"
              required
            />
            <input
              type="email"
              value={formData.email}
              onChange={event => handleFormChange('email', event.target.value)}
              placeholder="Email"
              aria-label="Email"
              required
            />
            <input
              value={formData.phone}
              onChange={event => handleFormChange('phone', event.target.value)}
              placeholder="Phone"
              aria-label="Phone"
              required
            />
            <select
              value={formData.department}
              onChange={event => handleFormChange('department', event.target.value)}
              aria-label="Department"
              required
            >
              <option value="">Select department</option>
              {departments.map(dep => (
                <option key={dep.id} value={String(dep.id)}>{dep.name}</option>
              ))}
            </select>
            <input
              value={formData.position}
              onChange={event => handleFormChange('position', event.target.value)}
              placeholder="Position"
              aria-label="Position"
              required
            />
            <select
              value={formData.employment_type}
              onChange={event => handleFormChange('employment_type', event.target.value)}
              aria-label="Employment type"
              required
            >
              <option value="FULL_TIME">Full-time</option>
              <option value="PART_TIME">Part-time</option>
              <option value="CONTRACTOR">Contractor</option>
            </select>
            <input
              type="date"
              value={formData.start_date}
              onChange={event => handleFormChange('start_date', event.target.value)}
              aria-label="Start date"
              required
            />
            <input
              type="number"
              step="0.01"
              value={formData.salary_ron}
              onChange={event => handleFormChange('salary_ron', event.target.value)}
              placeholder="Salary (RON)"
              aria-label="Salary RON"
              required
            />
            <input
              value={formData.address}
              onChange={event => handleFormChange('address', event.target.value)}
              placeholder="Address"
              aria-label="Address"
              required
            />
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={event => handleFormChange('is_active', event.target.checked)}
              />
              Active employee
            </label>

            {renderError('first_name')}
            {renderError('last_name')}
            {renderError('email')}
            {renderError('phone')}
            {renderError('department')}
            {renderError('position')}
            {renderError('employment_type')}
            {renderError('start_date')}
            {renderError('salary_ron')}
            {renderError('address')}
            {renderError('is_active')}
            {renderError('non_field_errors')}

            <div className="employee-form-actions">
              <button type="button" className="ghost-btn" onClick={handleCancel}>
                Cancel
              </button>
              <button type="submit" className="create-employee-btn" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Create Employee'}
              </button>
            </div>
          </form>
        </section>
      )}

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
