import { useEffect, useMemo, useState, type FormEvent } from 'react'

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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
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

    return <p className="text-[0.82rem] text-[var(--danger)]">{errors[0]}</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {toastMessage && <div className="fixed top-4 right-4 z-50 bg-[#1f9d60] text-white px-[0.9rem] py-[0.65rem] rounded-[10px] shadow-[0_10px_24px_rgba(0,0,0,0.16)] font-bold">{toastMessage}</div>}

      <div className="flex justify-between items-center gap-3">
        <div>
          <h2>Employee Directory</h2>
          <p>Track headcount with real-time filters and aggregated stats.</p>
        </div>s
        <button type="button" className="min-h-[40px] rounded-[10px] bg-[var(--accent)] text-white px-[0.95rem] font-bold cursor-pointer inline-flex items-center justify-center border-none disabled:opacity-70 disabled:cursor-not-allowed" onClick={() => setIsFormOpen(true)}>
          Register Employee
        </button>
      </div>

      {isFormOpen && (
        <section className="bg-white border border-[var(--border-app)] rounded-xl p-[0.8rem]">
          <h3>New Employee</h3>
          <form className="grid grid-cols-2 gap-[0.6rem]" onSubmit={handleSubmit}>
            <input
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
              value={formData.first_name}
              onChange={event => handleFormChange('first_name', event.target.value)}
              placeholder="First name"
              aria-label="First name"
              required
            />
            <input
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
              value={formData.last_name}
              onChange={event => handleFormChange('last_name', event.target.value)}
              placeholder="Last name"
              aria-label="Last name"
              required
            />
            <input
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
              type="email"
              value={formData.email}
              onChange={event => handleFormChange('email', event.target.value)}
              placeholder="Email"
              aria-label="Email"
              required
            />
            <input
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
              value={formData.phone}
              onChange={event => handleFormChange('phone', event.target.value)}
              placeholder="Phone"
              aria-label="Phone"
              required
            />
            <select
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
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
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
              value={formData.position}
              onChange={event => handleFormChange('position', event.target.value)}
              placeholder="Position"
              aria-label="Position"
              required
            />
            <select
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
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
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
              type="date"
              value={formData.start_date}
              onChange={event => handleFormChange('start_date', event.target.value)}
              aria-label="Start date"
              required
            />
            <input
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
              type="number"
              step="0.01"
              value={formData.salary_ron}
              onChange={event => handleFormChange('salary_ron', event.target.value)}
              placeholder="Salary (RON)"
              aria-label="Salary RON"
              required
            />
            <input
              className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
              value={formData.address}
              onChange={event => handleFormChange('address', event.target.value)}
              placeholder="Address"
              aria-label="Address"
              required
            />
            <label className="col-span-full inline-flex items-center gap-[0.45rem] text-[0.92rem] text-[var(--ink-subtle)]">
              <input
                className="w-4 h-4 min-h-[16px] p-0"
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

            <div className="col-span-full flex justify-end gap-[0.55rem] mt-[0.2rem]">
              <button type="button" className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] bg-white text-[var(--ink)] px-[0.9rem] font-semibold cursor-pointer" onClick={handleCancel}>
                Cancel
              </button>
              <button type="submit" className="min-h-[40px] rounded-[10px] bg-[var(--accent)] text-white px-[0.95rem] font-bold cursor-pointer inline-flex items-center justify-center border-none disabled:opacity-70 disabled:cursor-not-allowed" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Create Employee'}
              </button>
            </div>
          </form>
        </section>
      )}

      <div className="grid grid-cols-3 gap-3">
        <article className="bg-white border border-[var(--border-app)] rounded-xl px-[0.9rem] py-3 flex flex-col gap-[0.3rem]">
          <span className="text-[var(--ink-subtle)] text-[0.82rem]">Total Employees</span>
          <strong>{stats.total}</strong>
        </article>
        <article className="bg-white border border-[var(--border-app)] rounded-xl px-[0.9rem] py-3 flex flex-col gap-[0.3rem]">
          <span className="text-[var(--ink-subtle)] text-[0.82rem]">Active Employees</span>
          <strong>{stats.active}</strong>
        </article>
        <article className="bg-white border border-[var(--border-app)] rounded-xl px-[0.9rem] py-3 flex flex-col gap-[0.3rem]">
          <span className="text-[var(--ink-subtle)] text-[0.82rem]">Full-time Employees</span>
          <strong>{stats.full_time}</strong>
        </article>
      </div>

      <div className="grid grid-cols-[1fr_220px] gap-[0.6rem] bg-white border border-[var(--border-app)] rounded-xl p-[0.65rem]">
        <input
          className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
          value={departmentFilter}
          onChange={event => {
            setPage(1)
            setDepartmentFilter(event.target.value)
          }}
          placeholder="Filter by department slug (e.g. hr)"
          aria-label="Filter by department"
        />

        <select
          className="min-h-[40px] border border-[var(--border-app)] rounded-[10px] px-[0.7rem] bg-[var(--surface-soft)] text-[var(--ink)]"
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
        <section className="bg-white border border-[var(--border-app)] rounded-2xl p-5">Loading employees...</section>
      ) : employees.length === 0 ? (
        <section className="bg-white border border-[var(--border-app)] rounded-2xl px-[1.2rem] py-[2.2rem] min-h-[340px] flex flex-col items-center justify-center text-center gap-[0.7rem]">
          <h3>No employees found</h3>
          <p>Try clearing filters or add employees so headcount can be tracked.</p>
          <button
            type="button"
            className="border border-[var(--border-app)] bg-white text-[var(--ink)] rounded-[10px] px-3 py-[0.45rem] cursor-pointer font-semibold"
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
          <section className="bg-white border border-[var(--border-app)] rounded-2xl overflow-hidden">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[var(--ink-subtle)] font-bold text-[0.82rem] uppercase tracking-[0.04em]">Name</th>
                  <th className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[var(--ink-subtle)] font-bold text-[0.82rem] uppercase tracking-[0.04em]">Email</th>
                  <th className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[var(--ink-subtle)] font-bold text-[0.82rem] uppercase tracking-[0.04em]">Phone</th>
                  <th className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[var(--ink-subtle)] font-bold text-[0.82rem] uppercase tracking-[0.04em]">Position</th>
                  <th className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[var(--ink-subtle)] font-bold text-[0.82rem] uppercase tracking-[0.04em]">Department</th>
                  <th className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[var(--ink-subtle)] font-bold text-[0.82rem] uppercase tracking-[0.04em]">Status</th>
                </tr>
              </thead>
              <tbody>
                {employees.map(employee => (
                  <tr key={employee.id}>
                    <td className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[0.9rem]">{`${employee.first_name} ${employee.last_name}`.trim() || employee.username}</td>
                    <td className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[0.9rem]">{employee.email}</td>
                    <td className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[0.9rem]">{employee.phone}</td>
                    <td className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[0.9rem]">{employee.position}</td>
                    <td className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[0.9rem]">{employee.department?.name ?? 'Unassigned'}</td>
                    <td className="text-left px-[0.85rem] py-[0.72rem] border-b border-[var(--border-app)] text-[0.9rem]">{employee.is_active ? 'Active' : 'Inactive'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <div className="flex justify-between items-center gap-3 flex-wrap">
            <div className="flex flex-wrap gap-[0.4rem]">
              {stats.departments.map(dep => (
                <span key={dep.name} className="bg-white border border-[var(--border-app)] rounded-full px-[0.65rem] py-[0.28rem] text-[0.8rem] text-[var(--ink-subtle)]">{dep.name}: {dep.count}</span>
              ))}
            </div>

            <div className="inline-flex items-center gap-2">
              <button
                type="button"
                className="border border-[var(--border-app)] bg-white text-[var(--ink)] rounded-[10px] px-3 py-[0.45rem] cursor-pointer font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={page <= 1}
                onClick={() => setPage(current => Math.max(1, current - 1))}
              >
                Previous
              </button>
              <span>{`Page ${page} / ${totalPages}`}</span>
              <button
                type="button"
                className="border border-[var(--border-app)] bg-white text-[var(--ink)] rounded-[10px] px-3 py-[0.45rem] cursor-pointer font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
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
