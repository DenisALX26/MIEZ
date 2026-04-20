import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

type Department = {
  id: number
  name: string
  slug: string
}

type Employee = {
  id: number
  username: string
  first_name: string
  last_name: string
  role: string
  employment_type: 'FULL_TIME' | 'PART_TIME' | 'CONTRACTOR'
  is_active: boolean
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

const getDisplayName = (employee: Employee) => {
  const fullName = `${employee.first_name} ${employee.last_name}`.trim()
  return fullName || employee.username
}

const getInitials = (employee: Employee) => {
  const fullName = getDisplayName(employee)
  const parts = fullName.split(/\s+/).filter(Boolean)
  if (parts.length === 0) {
    return 'U'
  }

  const first = parts[0]?.[0] ?? ''
  const second = parts[1]?.[0] ?? ''
  return `${first}${second}`.toUpperCase() || 'U'
}

const formatRole = (role: string) => {
  if (role === 'SALES') return 'Sales'
  if (role === 'INVENTORY') return 'Inventory'
  return role
}

const formatContract = (employmentType: Employee['employment_type']) => {
  if (employmentType === 'FULL_TIME') return 'Full-time'
  if (employmentType === 'PART_TIME') return 'Part-time'
  return 'Contract'
}

const EmployeesPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [employees, setEmployees] = useState<Employee[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setDebouncedSearch(searchTerm.trim())
      setPage(1)
    }, 250)

    return () => window.clearTimeout(timeout)
  }, [searchTerm])

  useEffect(() => {
    const fetchEmployees = async () => {
      setIsLoading(true)
      try {
        const params = new URLSearchParams({ page: String(page) })

        if (departmentFilter) {
          params.set('department', departmentFilter)
        }
        if (debouncedSearch) {
          params.set('search', debouncedSearch)
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
      } catch (error) {
        console.error('Failed to load employees', error)
        setEmployees([])
        setTotal(0)
      } finally {
        setIsLoading(false)
      }
    }

    fetchEmployees()
  }, [page, departmentFilter, debouncedSearch])

  useEffect(() => {
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

    fetchDepartments()
  }, [])

  useEffect(() => {
    setPage(1)
  }, [departmentFilter])

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(total / 10))
  }, [total])

  const detailRouteBase = location.pathname.startsWith('/employees') ? '/employees' : '/hr/employees'

  return (
    <section className="flex flex-col gap-4">
      <header className="flex flex-col gap-1">
        <h2 className="text-[1.18rem] font-semibold">Employees</h2>
        <p className="text-[0.92rem] text-[var(--muted-foreground)]">
          Search and review employees by role, department, contract and status.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-[1fr_280px] gap-3">
        <input
          className="min-h-[42px] border border-[var(--border)] rounded-[10px] px-[0.8rem] bg-[var(--card)] text-[var(--card-foreground)]"
          value={searchTerm}
          onChange={event => setSearchTerm(event.target.value)}
          placeholder="Search by employee name"
          aria-label="Search employees by name"
        />

        <select
          className="min-h-[42px] border border-[var(--border)] rounded-[10px] px-[0.75rem] bg-[var(--card)] text-[var(--card-foreground)]"
          value={departmentFilter}
          onChange={event => setDepartmentFilter(event.target.value)}
          aria-label="Filter by department"
        >
          <option value="">All departments</option>
          {departments.map(department => (
            <option key={department.id} value={department.slug}>{department.name}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">Loading employees...</section>
      ) : employees.length === 0 ? (
        <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">No employees found for current filters.</section>
      ) : (
        <>
          <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl overflow-hidden">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="text-left px-4 py-3 border-b border-[var(--border)] text-[0.8rem] text-[var(--muted-foreground)] uppercase tracking-[0.05em]">Avatar + Name</th>
                  <th className="text-left px-4 py-3 border-b border-[var(--border)] text-[0.8rem] text-[var(--muted-foreground)] uppercase tracking-[0.05em]">Role</th>
                  <th className="text-left px-4 py-3 border-b border-[var(--border)] text-[0.8rem] text-[var(--muted-foreground)] uppercase tracking-[0.05em]">Department</th>
                  <th className="text-left px-4 py-3 border-b border-[var(--border)] text-[0.8rem] text-[var(--muted-foreground)] uppercase tracking-[0.05em]">Contract</th>
                  <th className="text-left px-4 py-3 border-b border-[var(--border)] text-[0.8rem] text-[var(--muted-foreground)] uppercase tracking-[0.05em]">Status</th>
                </tr>
              </thead>
              <tbody>
                {employees.map(employee => (
                  <tr
                    key={employee.id}
                    className="cursor-pointer hover:bg-black/5 transition-colors"
                    onClick={() => navigate(`${detailRouteBase}/${employee.id}`)}
                  >
                    <td className="px-4 py-3 border-b border-[var(--border)]">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-[var(--primary)] text-[var(--primary-foreground)] grid place-items-center text-[0.8rem] font-bold">
                          {getInitials(employee)}
                        </div>
                        <span className="font-medium">{getDisplayName(employee)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 border-b border-[var(--border)]">{formatRole(employee.role)}</td>
                    <td className="px-4 py-3 border-b border-[var(--border)]">{employee.department?.name ?? 'Unassigned'}</td>
                    <td className="px-4 py-3 border-b border-[var(--border)]">{formatContract(employee.employment_type)}</td>
                    <td className="px-4 py-3 border-b border-[var(--border)]">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-1 text-[0.76rem] font-semibold ${employee.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-200 text-gray-700'}`}
                      >
                        {employee.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <div className="inline-flex items-center gap-2 self-end">
            <button
              type="button"
              className="border border-[var(--border)] bg-[var(--card)] text-[var(--card-foreground)] rounded-[10px] px-3 py-[0.45rem] cursor-pointer font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={page <= 1}
              onClick={() => setPage(current => Math.max(1, current - 1))}
            >
              Previous
            </button>
            <span className="text-[0.9rem]">{`Page ${page} / ${totalPages}`}</span>
            <button
              type="button"
              className="border border-[var(--border)] bg-[var(--card)] text-[var(--card-foreground)] rounded-[10px] px-3 py-[0.45rem] cursor-pointer font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={page >= totalPages}
              onClick={() => setPage(current => Math.min(totalPages, current + 1))}
            >
              Next
            </button>
          </div>
        </>
      )}
    </section>
  )
}

export default EmployeesPage
