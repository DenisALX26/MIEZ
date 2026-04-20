import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

type Employee = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  phone: string
  position: string
  employment_type: 'FULL_TIME' | 'PART_TIME' | 'CONTRACTOR'
  start_date: string
  salary_ron: string
  address: string
  role: string
  is_active: boolean
  department: null | {
    id: number
    name: string
    slug: string
  }
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

const EmployeeDetailPage = () => {
  const navigate = useNavigate()
  const { id } = useParams()
  const [employee, setEmployee] = useState<Employee | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchEmployee = async () => {
      if (!id) {
        setError('Missing employee id.')
        setIsLoading(false)
        return
      }

      try {
        setIsLoading(true)
        setError('')

        const response = await fetch(`/api/employees/${id}/`, {
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error(`Failed to load employee detail: ${response.status}`)
        }

        const data = (await response.json()) as Employee
        setEmployee(data)
      } catch (fetchError) {
        console.error('Failed to load employee detail', fetchError)
        setError('Could not load employee details right now.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchEmployee()
  }, [id])

  const displayName = useMemo(() => {
    if (!employee) {
      return ''
    }

    const fullName = `${employee.first_name} ${employee.last_name}`.trim()
    return fullName || employee.username
  }, [employee])

  if (isLoading) {
    return <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5">Loading employee details...</section>
  }

  if (error || !employee) {
    return (
      <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 flex flex-col gap-3">
        <p>{error || 'Employee not found.'}</p>
        <button
          type="button"
          className="self-start border border-[var(--border)] bg-[var(--card)] text-[var(--card-foreground)] rounded-[10px] px-3 py-[0.45rem] cursor-pointer font-semibold"
          onClick={() => navigate(-1)}
        >
          Back
        </button>
      </section>
    )
  }

  return (
    <section className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 flex flex-col gap-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-[1.18rem] font-semibold">{displayName}</h2>
          <p className="text-[0.92rem] text-[var(--muted-foreground)]">Employee details</p>
        </div>
        <button
          type="button"
          className="border border-[var(--border)] bg-[var(--card)] text-[var(--card-foreground)] rounded-[10px] px-3 py-[0.45rem] cursor-pointer font-semibold"
          onClick={() => navigate(-1)}
        >
          Back to list
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <article className="border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.8rem] text-[var(--muted-foreground)]">Role</p>
          <p className="font-medium mt-1">{formatRole(employee.role)}</p>
        </article>
        <article className="border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.8rem] text-[var(--muted-foreground)]">Department</p>
          <p className="font-medium mt-1">{employee.department?.name ?? 'Unassigned'}</p>
        </article>
        <article className="border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.8rem] text-[var(--muted-foreground)]">Contract Type</p>
          <p className="font-medium mt-1">{formatContract(employee.employment_type)}</p>
        </article>
        <article className="border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.8rem] text-[var(--muted-foreground)]">Status</p>
          <p className="font-medium mt-1">{employee.is_active ? 'Active' : 'Inactive'}</p>
        </article>
        <article className="border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.8rem] text-[var(--muted-foreground)]">Email</p>
          <p className="font-medium mt-1">{employee.email || '-'}</p>
        </article>
        <article className="border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.8rem] text-[var(--muted-foreground)]">Phone</p>
          <p className="font-medium mt-1">{employee.phone || '-'}</p>
        </article>
        <article className="border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.8rem] text-[var(--muted-foreground)]">Position</p>
          <p className="font-medium mt-1">{employee.position || '-'}</p>
        </article>
        <article className="border border-[var(--border)] rounded-xl p-4">
          <p className="text-[0.8rem] text-[var(--muted-foreground)]">Start Date</p>
          <p className="font-medium mt-1">{employee.start_date || '-'}</p>
        </article>
      </div>
    </section>
  )
}

export default EmployeeDetailPage
